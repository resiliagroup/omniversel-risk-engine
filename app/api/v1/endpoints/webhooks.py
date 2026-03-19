"""Webhook endpoints — event-driven URI recalculation triggers."""

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import structlog

from app.db.base import AsyncSessionLocal
from app.models.facility import Facility
from app.schemas.risk import (
    AssessmentCreateRequest,
    HazardInputSchema,
    FragilityInputSchema,
    ExposureInputSchema,
    ResponseCapacityInputSchema,
)
from app.services.risk.scoring_pipeline import pipeline

router = APIRouter()
logger = structlog.get_logger()


class NearMissEvent(BaseModel):
    facility_id: UUID
    near_miss_count: int
    tenant_id: UUID


async def recalculate_uri(facility_id: str, near_miss_count: int) -> None:
    """Background task: rebuild URI from facility extra_data + new near_miss_count."""
    log = logger.bind(facility_id=facility_id, near_miss_count=near_miss_count)
    log.info("webhook.recalculate_uri.start")

    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Facility)
                .where(Facility.id == UUID(facility_id))
                .options(selectinload(Facility.location_data))
            )
            facility = result.scalar_one_or_none()
            if not facility:
                log.warning("webhook.facility_not_found")
                return

            ex = facility.extra_data or {}

            # Derive hazard scores from extra_data (stored by resilia-platform form)
            deprem = float(ex.get("risk_deprem", ex.get("H_score", 2.5)))
            sel    = float(ex.get("risk_sel", 1.5))
            natech = float(ex.get("natech_risk", 1.0))
            cyber  = float(ex.get("risk_siber", 1.5))

            primary_hazard = (
                "natech" if ex.get("hazmat_flag") else
                "deprem"  if deprem >= sel else "sel"
            )
            hazmat = bool(ex.get("hazmat_flag", False))

            # Map extra_data scores (1-5 range) → 0-100 range for schema
            def s(v: float) -> float:
                return min(100.0, float(v) * 20.0)

            f_score = float(ex.get("F_score", 2.5))
            c_score = float(ex.get("C_score", 2.0))

            request = AssessmentCreateRequest(
                facility_id=UUID(facility_id),
                hazard=HazardInputSchema(
                    seismic=s(deprem),
                    flood=s(sel),
                    supply_chain=s(natech),
                    cyber=s(cyber),
                ),
                fragility=FragilityInputSchema(
                    building_age_score=s(f_score),
                    construction_quality=s(f_score),
                ),
                exposure=ExposureInputSchema(
                    population_at_risk=facility.employee_count or 100,
                    asset_criticality=min(1.0, float(ex.get("X_score", 2.5)) / 5.0),
                ),
                response=ResponseCapacityInputSchema(
                    bcm_plan_exists=c_score >= 2,
                    plan_tested_last_12m=c_score >= 3,
                    drill_frequency_per_year=round(c_score),
                    crisis_team_exists=c_score >= 3,
                ),
                bottleneck_score=2.5 if hazmat else 1.2,
                near_miss_count=near_miss_count,
                tatbikat_var=False,
                otonom_squad=False,
                primary_hazard=primary_hazard,
                notes="auto_near_miss_trigger",
            )

            assessment, _ = await pipeline.run(db=db, facility=facility, request=request)
            log.info(
                "webhook.recalculate_uri.complete",
                uri_score=assessment.uri_score,
                hro_alpha=assessment.hro_alpha,
            )

    except Exception as exc:
        log.error("webhook.recalculate_uri.error", error=str(exc), exc_info=True)


@router.post("/near-miss-trigger")
async def near_miss_trigger(event: NearMissEvent, background_tasks: BackgroundTasks):
    """
    Fired by resilia-platform after a near-miss event is saved to Supabase.
    Triggers background URI recalculation and persists updated assessment to DB.
    """
    background_tasks.add_task(
        recalculate_uri,
        str(event.facility_id),
        event.near_miss_count,
    )
    return {
        "status": "triggered",
        "facility_id": str(event.facility_id),
        "near_miss_count": event.near_miss_count,
    }
