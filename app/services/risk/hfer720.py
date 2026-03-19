"""
OMNI Risk Intelligence Engine
HFER-720 Classical Risk Model
─────────────────────────────
Four-dimensional risk scoring:
  H — Hazard
  F — Fragility
  E — Exposure
  R — Response Capacity

Output: Unified Risk Index (URI) 0-100
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field

from app.core.constants import (
    SectorType, HazardType, SECTOR_WEIGHTS,
    HAZARD_DEFINITIONS, classify_risk, RISK_REVIEW_DAYS,
    FRAGILITY_SUBWEIGHTS, RESPONSE_SUBWEIGHTS,
)
from app.schemas.risk import (
    FragilityInput, ExposureInput, ResponseCapacityInput,
    HazardScoreInput, HazardBreakdown, RadarData,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# K-MATRIX: sektör × tehlike katsayı matrisi
# ─────────────────────────────────────────────

DEFAULT_K_MATRIX: dict[str, dict[str, float]] = {
    "HOSPITAL":     {"deprem": 2.8, "sel": 2.1, "natech": 3.5, "siber": 4.2},
    "INDUSTRIAL":   {"deprem": 3.2, "sel": 2.8, "natech": 4.8, "siber": 1.9},
    "BANK":         {"deprem": 1.8, "sel": 1.5, "natech": 2.0, "siber": 5.1},
    "MUNICIPALITY": {"deprem": 3.0, "sel": 2.5, "natech": 3.2, "siber": 3.8},
    "EDUCATION":    {"deprem": 2.5, "sel": 2.0, "natech": 1.8, "siber": 2.2},
    "HOTEL":        {"deprem": 2.2, "sel": 3.0, "natech": 2.5, "siber": 2.8},
}

# Sektör adı → k-matrix anahtarı eşlemesi
_SECTOR_TO_K_KEY: dict[str, str] = {
    "hospital":     "HOSPITAL",
    "saglik":       "HOSPITAL",
    "industrial":   "INDUSTRIAL",
    "sanayi":       "INDUSTRIAL",
    "bank":         "BANK",
    "bankacilik":   "BANK",
    "municipality": "MUNICIPALITY",
    "belediye":     "MUNICIPALITY",
    "education":    "EDUCATION",
    "egitim":       "EDUCATION",
    "hotel":        "HOTEL",
    "konaklama":    "HOTEL",
}


def compute_hro_alpha(
    near_miss_count: int = 0,
    tatbikat_var: bool = False,
    otonom_squad: bool = False,
) -> float:
    """
    HRO olgunluk katsayısı (α):
      near_miss_count > 0  → 1.2  (raporlama kültürü aktif)
      tatbikat_var         → 1.1  (proaktif hazırlık)
      otonom_squad         → 1.3  (merkeziyetsiz karar alma)
      varsayılan           → 0.8
    Birden fazla koşul varsa en yüksek değer alınır.
    """
    alpha = 0.8
    if near_miss_count > 0:
        alpha = max(alpha, 1.2)
    if tatbikat_var:
        alpha = max(alpha, 1.1)
    if otonom_squad:
        alpha = max(alpha, 1.3)
    return round(alpha, 2)


def _load_k_matrix() -> dict:
    """Override dosyası varsa onu yükle, yoksa DEFAULT_K_MATRIX döndür."""
    import json, os
    _K_OVERRIDE = "/tmp/k_matrix_override.json"
    if os.path.exists(_K_OVERRIDE):
        try:
            with open(_K_OVERRIDE) as f:
                data = json.load(f)
            return data.get("sector_matrix", DEFAULT_K_MATRIX)
        except Exception:
            pass
    return DEFAULT_K_MATRIX


def get_k_value(sector: str, hazard: str, k_matrix: dict | None = None) -> float:
    """k(s,t): sektör-tehlike katsayısını döner.
    Öncelik sırası: çağıran tarafından verilen k_matrix → /tmp override → DEFAULT_K_MATRIX.
    """
    matrix = k_matrix or _load_k_matrix()
    k_key = _SECTOR_TO_K_KEY.get(sector.lower(), sector.upper())
    row = matrix.get(k_key, {})
    return row.get(hazard.lower(), 1.0)


# ─────────────────────────────────────────────
# SCORE RESULTS
# ─────────────────────────────────────────────

@dataclass
class HFER720Result:
    h_score: float          # Hazard score (0-100, higher = more hazard)
    f_score: float          # Fragility score (0-100)
    e_score: float          # Exposure score (0-100)
    r_score: float          # Response capacity (0-100, higher = better)
    uri_score: float        # Unified Risk Index (0-100, higher = safer)
    risk_class: str
    confidence: float
    hazard_breakdown: list[HazardBreakdown]
    radar: RadarData
    score_breakdown: dict   # full audit trail
    hro_alpha: float = 0.8         # HRO olgunluk katsayısı
    bottleneck_score: float = 1.0  # TOC darboğaz çarpanı


# ─────────────────────────────────────────────
# HAZARD SCORER
# ─────────────────────────────────────────────

class HazardScorer:
    """
    Computes composite Hazard (H) score from multi-hazard inputs.
    H_composite = Σ (probability_i × intensity_i × global_weight_i)
    """

    def score(self, hazard_inputs: list[HazardScoreInput]) -> tuple[float, list[HazardBreakdown]]:
        if not hazard_inputs:
            logger.warning("No hazard inputs provided — using default score 50")
            return 50.0, []

        # Build lookup from inputs
        input_map = {h.hazard_type: h for h in hazard_inputs}

        total_weight = 0.0
        weighted_sum = 0.0
        breakdowns: list[HazardBreakdown] = []

        for hdef in HAZARD_DEFINITIONS:
            h_input = input_map.get(hdef.hazard_type.value)
            if h_input is None:
                # Use default moderate values if not provided
                prob, intensity = 0.3, 40.0
                source = "default"
            else:
                prob = h_input.probability
                intensity = h_input.intensity
                source = h_input.data_source or "manual"

            raw_score = prob * intensity  # 0-100 range
            weighted_contribution = raw_score * hdef.global_weight

            weighted_sum += weighted_contribution
            total_weight += hdef.global_weight

            breakdowns.append(HazardBreakdown(
                hazard_type=hdef.hazard_type.value,
                score=round(raw_score, 2),
                probability=prob,
                intensity=intensity,
                data_source=source,
            ))

        composite = (weighted_sum / total_weight) if total_weight > 0 else 50.0
        return round(min(max(composite, 0), 100), 2), breakdowns


# ─────────────────────────────────────────────
# FRAGILITY SCORER
# ─────────────────────────────────────────────

class FragilityScorer:
    """
    Computes Fragility (F) score across 4 sub-dimensions.
    Higher score = more fragile = higher risk.
    """

    def score(self, f: FragilityInput) -> tuple[float, dict]:
        structural = self._score_structural(f)
        operational = self._score_operational(f)
        human = self._score_human(f)
        digital = self._score_digital(f)

        composite = (
            structural   * FRAGILITY_SUBWEIGHTS["structural"] +
            operational  * FRAGILITY_SUBWEIGHTS["operational"] +
            human        * FRAGILITY_SUBWEIGHTS["human"] +
            digital      * FRAGILITY_SUBWEIGHTS["digital"]
        )

        breakdown = {
            "structural": round(structural, 2),
            "operational": round(operational, 2),
            "human": round(human, 2),
            "digital": round(digital, 2),
        }

        return round(min(max(composite, 0), 100), 2), breakdown

    def _score_structural(self, f: FragilityInput) -> float:
        score = 50.0  # baseline

        # Building age penalty
        if f.building_age:
            if f.building_age > 40:   score += 20
            elif f.building_age > 25: score += 10
            elif f.building_age > 10: score += 5

        # Construction type
        construction_penalties = {
            "masonry": 20, "wood": 25, "RC": 0, "steel": -5
        }
        if f.construction_type:
            score += construction_penalties.get(f.construction_type, 5)

        # Inspection recency
        if f.last_inspection_years:
            if f.last_inspection_years > 5:  score += 15
            elif f.last_inspection_years > 2: score += 5

        # Mitigation credit
        if f.structural_reinforced: score -= 15

        return min(max(score, 0), 100)

    def _score_operational(self, f: FragilityInput) -> float:
        score = 50.0

        if not f.has_backup_power:    score += 15
        if not f.has_redundant_systems: score += 10
        score += min(f.single_points_of_failure * 8, 30)

        # Maintenance quality
        score -= (f.maintenance_score - 50) * 0.4  # 0-100 → -20 to +20

        return min(max(score, 0), 100)

    def _score_human(self, f: FragilityInput) -> float:
        score = 50.0

        # Training coverage
        if f.bcm_trained_staff_pct < 20:   score += 20
        elif f.bcm_trained_staff_pct < 50: score += 10
        elif f.bcm_trained_staff_pct > 80: score -= 15

        # Staff turnover (high turnover = knowledge loss)
        if f.staff_turnover_annual > 30:   score += 15
        elif f.staff_turnover_annual > 15: score += 7

        if not f.has_crisis_team: score += 10

        return min(max(score, 0), 100)

    def _score_digital(self, f: FragilityInput) -> float:
        score = 50.0

        # Cyber hygiene (0-100 → modifier)
        score -= (f.cyber_hygiene_score - 50) * 0.5

        if not f.has_offsite_backup: score += 20

        if f.it_system_age_years:
            if f.it_system_age_years > 7:  score += 15
            elif f.it_system_age_years > 3: score += 5

        return min(max(score, 0), 100)


# ─────────────────────────────────────────────
# EXPOSURE SCORER
# ─────────────────────────────────────────────

class ExposureScorer:
    """
    Computes Exposure (E) score.
    Factors in population, asset value, cascade dependencies.
    """

    def score(self, e: ExposureInput) -> tuple[float, dict]:
        pop_score    = self._score_population(e)
        asset_score  = self._score_assets(e)
        dep_score    = self._score_dependencies(e)

        composite = (
            pop_score   * 0.35 +
            asset_score * 0.35 +
            dep_score   * 0.30
        )

        breakdown = {
            "population": round(pop_score, 2),
            "assets": round(asset_score, 2),
            "dependencies": round(dep_score, 2),
        }

        return round(min(max(composite, 0), 100), 2), breakdown

    def _score_population(self, e: ExposureInput) -> float:
        if e.population_at_risk == 0:
            return 20.0

        # Log-scaled population score
        import math
        pop_score = min(math.log10(max(e.population_at_risk, 1)) * 20, 80)
        return pop_score * (0.5 + e.population_vulnerability * 0.5)

    def _score_assets(self, e: ExposureInput) -> float:
        if not e.asset_value_tl:
            return 40.0  # unknown = moderate default

        import math
        asset_score = min(math.log10(max(e.asset_value_tl, 1)) * 8, 80)
        return asset_score * (0.5 + e.asset_replacement_difficulty * 0.5)

    def _score_dependencies(self, e: ExposureInput) -> float:
        # Each critical service dependency adds to exposure
        dep_score = min(e.critical_services_count * 10, 60)

        # External dependency facilities add cascade risk
        cascade_factor = min(len(e.dependency_facility_ids) * 5, 40)
        dep_score += cascade_factor

        return min(dep_score, 100)


# ─────────────────────────────────────────────
# RESPONSE CAPACITY SCORER
# ─────────────────────────────────────────────

class ResponseCapacityScorer:
    """
    Computes Response Capacity (R) score.
    Higher = better prepared = lower overall risk.
    """

    def score(self, r: ResponseCapacityInput) -> tuple[float, dict]:
        plan_score      = self._score_plans(r)
        resource_score  = self._score_resources(r)
        training_score  = self._score_training(r)
        network_score   = self._score_network(r)

        composite = (
            plan_score     * RESPONSE_SUBWEIGHTS["plans"] +
            resource_score * RESPONSE_SUBWEIGHTS["resources"] +
            training_score * RESPONSE_SUBWEIGHTS["training"] +
            network_score  * RESPONSE_SUBWEIGHTS["network"]
        )

        breakdown = {
            "plans": round(plan_score, 2),
            "resources": round(resource_score, 2),
            "training": round(training_score, 2),
            "network": round(network_score, 2),
        }

        return round(min(max(composite, 0), 100), 2), breakdown

    def _score_plans(self, r: ResponseCapacityInput) -> float:
        score = 0.0

        if r.has_bcm_plan:
            score += 20
            if r.plan_last_tested_months is not None:
                if r.plan_last_tested_months <= 12: score += 25
                elif r.plan_last_tested_months <= 24: score += 12
            if r.iso_22301_certified: score += 30
            if r.plan_is_digital: score += 25

        return min(score, 100)

    def _score_resources(self, r: ResponseCapacityInput) -> float:
        score = 0.0

        # Emergency supplies
        if r.emergency_supplies_days >= 7:  score += 30
        elif r.emergency_supplies_days >= 3: score += 15
        elif r.emergency_supplies_days >= 1: score += 5

        if r.backup_site_available: score += 30

        # Equipment readiness (0-100 → 0-40 contribution)
        score += r.equipment_readiness * 0.4

        return min(score, 100)

    def _score_training(self, r: ResponseCapacityInput) -> float:
        score = 0.0

        # Annual drills
        if r.drill_frequency_annual >= 4:   score += 40
        elif r.drill_frequency_annual >= 2: score += 25
        elif r.drill_frequency_annual >= 1: score += 10

        # Certified staff
        score += min(r.certified_staff_count * 5, 30)

        # Drill recency
        if r.last_drill_months is not None:
            if r.last_drill_months <= 6:  score += 30
            elif r.last_drill_months <= 12: score += 15

        return min(score, 100)

    def _score_network(self, r: ResponseCapacityInput) -> float:
        score = 0.0

        # Mutual aid agreements
        score += min(r.mutual_aid_agreements * 15, 60)

        # External coordination
        score += r.external_coordination_score * 0.4

        return min(score, 100)


# ─────────────────────────────────────────────
# HFER-720 MAIN ENGINE
# ─────────────────────────────────────────────

class HFER720Engine:
    """
    Main classical risk model.
    Composes H, F, E, R into a Unified Risk Index (URI).

    URI = (H × F × E × B) / (1 + k(s,t) × C²) × HRO_α
    where:
      B   = bottleneck_score (TOC darboğaz çarpanı, 1.0-3.0)
      k   = sektör × tehlike katsayısı (k_matrix)
      C   = normalised response deficit  (1 - r_score/100)
      α   = HRO olgunluk katsayısı (0.5-1.5)
    Result is re-scaled to 0-100, higher = safer.
    """

    def __init__(self):
        self.hazard_scorer   = HazardScorer()
        self.fragility_scorer = FragilityScorer()
        self.exposure_scorer = ExposureScorer()
        self.response_scorer = ResponseCapacityScorer()

    def compute(
        self,
        sector: str,
        hazard_inputs: list[HazardScoreInput],
        fragility: FragilityInput,
        exposure: ExposureInput,
        response: ResponseCapacityInput,
        bottleneck_score: float = 1.0,
        near_miss_count: int = 0,
        tatbikat_var: bool = False,
        otonom_squad: bool = False,
        k_matrix: dict | None = None,
        primary_hazard: str = "deprem",
    ) -> HFER720Result:

        sector_type = SectorType(sector) if sector in SectorType._value2member_map_ else SectorType.MUNICIPALITY
        weights = SECTOR_WEIGHTS[sector_type]

        # Score each dimension
        h_score, hazard_breakdown = self.hazard_scorer.score(hazard_inputs)
        f_score, f_breakdown = self.fragility_scorer.score(fragility)
        e_score, e_breakdown = self.exposure_scorer.score(exposure)
        r_score, r_breakdown = self.response_scorer.score(response)

        # ── HRO alpha & k(s,t) ────────────────────────────────
        hro_alpha = compute_hro_alpha(near_miss_count, tatbikat_var, otonom_squad)
        k_val = get_k_value(sector, primary_hazard, k_matrix)

        # ── New URI formula ───────────────────────────────────
        # C = response deficit (0 = perfect response, 1 = no response)
        c_deficit = 1.0 - (r_score / 100.0)

        # Raw risk numerator: product of risk dimensions × TOC bottleneck
        # Dimensions normalised to 0-1 range for multiplication
        h_n = h_score / 100.0
        f_n = f_score / 100.0
        e_n = e_score / 100.0
        b_n = min(max(bottleneck_score, 1.0), 3.0)

        raw_product = h_n * f_n * e_n * b_n  # 0-3 range

        # k(s,t) × C² dampens risk when response is strong
        denominator = 1.0 + k_val * (c_deficit ** 2)

        adjusted_risk = raw_product / denominator  # still 0-3 range roughly

        # Apply HRO alpha (>1 = safer, <1 = riskier)
        adjusted_risk = adjusted_risk / hro_alpha

        # Re-scale to URI 0-100 (higher = safer):
        # max theoretical adjusted_risk ≈ 3/(1*0.8) ≈ 3.75 → cap at 4 for normalisation
        uri_raw = 100.0 * (1.0 - min(adjusted_risk / 4.0, 1.0))
        uri_score = round(min(max(uri_raw, 0), 100), 2)

        risk_class = classify_risk(uri_score)

        radar = RadarData(
            hazard=round(h_score, 1),
            fragility=round(f_score, 1),
            exposure=round(e_score, 1),
            response=round(r_score, 1),
        )

        score_breakdown = {
            "sector": sector,
            "formula": "URI = (H×F×E×B) / (1 + k(s,t)×C²) × HRO_α",
            "weights": {
                "w_hazard": weights.w_hazard,
                "w_fragility": weights.w_fragility,
                "w_exposure": weights.w_exposure,
                "w_response": weights.w_response,
            },
            "hro_alpha": hro_alpha,
            "bottleneck_score": b_n,
            "k_value": k_val,
            "primary_hazard": primary_hazard,
            "c_deficit": round(c_deficit, 4),
            "raw_product": round(raw_product, 6),
            "adjusted_risk": round(adjusted_risk, 6),
            "hazard_detail": hazard_breakdown,
            "fragility_detail": f_breakdown,
            "exposure_detail": e_breakdown,
            "response_detail": r_breakdown,
        }

        return HFER720Result(
            h_score=h_score,
            f_score=f_score,
            e_score=e_score,
            r_score=r_score,
            uri_score=uri_score,
            risk_class=risk_class.value,
            confidence=0.85,   # classical model — fixed confidence
            hazard_breakdown=hazard_breakdown,
            radar=radar,
            score_breakdown=score_breakdown,
            hro_alpha=hro_alpha,
            bottleneck_score=b_n,
        )
