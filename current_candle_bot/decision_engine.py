"""
Decision Engine Module
Implements precision-first filtering and alert decision logic
"""
import time
from typing import Dict, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Decision(Enum):
    """Alert decision types."""
    ALERT_BULL = "ALERT_BULL"
    ALERT_BEAR = "ALERT_BEAR"
    NO_ALERT = "NO_ALERT"


class DecisionEngine:
    """
    Makes alert decisions based on model confidence, filters, and regime.
    Implements precision-first approach with multiple gates.
    """
    
    def __init__(
        self,
        bull_threshold: float = 0.65,
        bear_threshold: float = 0.65,
        min_body_pct: float = 0.0010,
        min_range_pct: float = 0.0012,
        min_vol_pctile: float = 60.0,
        cooldown_minutes: int = 10,
        hysteresis_margin: float = 0.03,
    ):
        """
        Initialize decision engine.
        
        Args:
            bull_threshold: Base threshold for bullish alerts
            bear_threshold: Base threshold for bearish alerts
            min_body_pct: Minimum candle body size (% of price)
            min_range_pct: Minimum candle range (% of price)
            min_vol_pctile: Minimum volume percentile
            cooldown_minutes: Minutes to wait between alerts
            hysteresis_margin: Margin to prevent flip-flop alerts
        """
        self.bull_threshold = bull_threshold
        self.bear_threshold = bear_threshold
        self.min_body_pct = min_body_pct
        self.min_range_pct = min_range_pct
        self.min_vol_pctile = min_vol_pctile
        self.cooldown_minutes = cooldown_minutes
        self.hysteresis_margin = hysteresis_margin
        
        # State tracking
        self.last_alert_time = 0
        self.last_alert_direction = None
        self.total_alerts_sent = 0
    
    def check_strength_filter(self, candle_info: Dict) -> Tuple[bool, str]:
        """
        Check if candle has sufficient strength.
        
        Args:
            candle_info: Dictionary with candle metrics
            
        Returns:
            Tuple of (passed, reason)
        """
        body_pct = candle_info.get('body_pct', 0)
        range_pct = candle_info.get('range_pct', 0)
        
        if body_pct < self.min_body_pct:
            return False, f"weak_body ({body_pct:.4f} < {self.min_body_pct})"
        
        if range_pct < self.min_range_pct:
            return False, f"weak_range ({range_pct:.4f} < {self.min_range_pct})"
        
        return True, "strength_ok"
    
    def check_volume_filter(self, candle_info: Dict) -> Tuple[bool, str]:
        """
        Check if candle has sufficient volume.
        
        Args:
            candle_info: Dictionary with candle metrics
            
        Returns:
            Tuple of (passed, reason)
        """
        vol_pctile = candle_info.get('volume_pctile', 0)
        
        if vol_pctile < self.min_vol_pctile:
            return False, f"low_volume ({vol_pctile:.1f} < {self.min_vol_pctile})"
        
        return True, "volume_ok"
    
    def check_cooldown(self) -> Tuple[bool, str]:
        """
        Check if cooldown period has passed.
        
        Returns:
            Tuple of (can_alert, reason)
        """
        current_time = time.time()
        time_since_last = (current_time - self.last_alert_time) / 60  # minutes
        
        if time_since_last < self.cooldown_minutes:
            remaining = self.cooldown_minutes - time_since_last
            return False, f"cooldown ({remaining:.1f}m remaining)"
        
        return True, "cooldown_ok"
    
    def check_hysteresis(self, direction: str, confidence: float) -> Tuple[bool, str]:
        """
        Check hysteresis to prevent flip-flop alerts.
        
        Args:
            direction: "BULL" or "BEAR"
            confidence: Model confidence
            
        Returns:
            Tuple of (passed, reason)
        """
        # If last alert was opposite direction, require extra margin
        if self.last_alert_direction is not None:
            if self.last_alert_direction != direction:
                # Require confidence above threshold + margin
                threshold = (
                    self.bull_threshold if direction == "BULL"
                    else self.bear_threshold
                )
                
                required_conf = threshold + self.hysteresis_margin
                
                if confidence < required_conf:
                    return False, f"hysteresis ({confidence:.3f} < {required_conf:.3f})"
        
        return True, "hysteresis_ok"
    
    def apply_regime_thresholds(
        self,
        regime: str,
        regime_thresholds: Optional[Dict] = None
    ) -> Tuple[float, float]:
        """
        Get regime-adjusted thresholds.
        
        Args:
            regime: Current market regime
            regime_thresholds: Optional dict of regime-specific thresholds
            
        Returns:
            Tuple of (bull_threshold, bear_threshold)
        """
        if regime_thresholds and regime in regime_thresholds:
            thresholds = regime_thresholds[regime]
            return thresholds.get('bull', self.bull_threshold), thresholds.get('bear', self.bear_threshold)
        
        # Default regime adjustments
        adjustments = {
            'TREND': 1.0,
            'CHOP': 1.15,
            'HIGH_VOL_TREND': 0.95,
            'HIGH_VOL_CHOP': 1.20,
            'UNKNOWN': 1.10,
        }
        
        factor = adjustments.get(regime, 1.0)
        
        return (
            min(self.bull_threshold * factor, 0.95),
            min(self.bear_threshold * factor, 0.95)
        )
    
    def decide(
        self,
        prob_up: float,
        prob_up_smoothed: float,
        candle_info: Dict,
        regime: str,
        regime_thresholds: Optional[Dict] = None,
        use_smoothed: bool = True
    ) -> Tuple[Decision, str, Dict]:
        """
        Make alert decision with all filters.
        
        Args:
            prob_up: Raw probability of green candle
            prob_up_smoothed: Smoothed probability
            candle_info: Candle strength/volume info
            regime: Current market regime
            regime_thresholds: Optional regime-specific thresholds
            use_smoothed: Use smoothed confidence for decision
            
        Returns:
            Tuple of (decision, reason, details)
        """
        # Use smoothed or raw confidence
        confidence = prob_up_smoothed if use_smoothed else prob_up
        
        # Get regime-adjusted thresholds
        bull_thresh, bear_thresh = self.apply_regime_thresholds(regime, regime_thresholds)
        
        # Determine direction
        if confidence > bull_thresh:
            direction = "BULL"
            threshold_used = bull_thresh
        elif (1 - confidence) > bear_thresh:
            direction = "BEAR"
            threshold_used = bear_thresh
        else:
            return (
                Decision.NO_ALERT,
                "below_threshold",
                {
                    'confidence': confidence,
                    'bull_threshold': bull_thresh,
                    'bear_threshold': bear_thresh,
                }
            )
        
        # Apply filters
        filters_passed = []
        
        # 1. Strength filter
        strength_ok, strength_reason = self.check_strength_filter(candle_info)
        if not strength_ok:
            return Decision.NO_ALERT, strength_reason, {'confidence': confidence}
        filters_passed.append('strength')
        
        # 2. Volume filter
        volume_ok, volume_reason = self.check_volume_filter(candle_info)
        if not volume_ok:
            return Decision.NO_ALERT, volume_reason, {'confidence': confidence}
        filters_passed.append('volume')
        
        # 3. Cooldown check
        cooldown_ok, cooldown_reason = self.check_cooldown()
        if not cooldown_ok:
            return Decision.NO_ALERT, cooldown_reason, {'confidence': confidence}
        filters_passed.append('cooldown')
        
        # 4. Hysteresis check
        hysteresis_ok, hysteresis_reason = self.check_hysteresis(direction, confidence)
        if not hysteresis_ok:
            return Decision.NO_ALERT, hysteresis_reason, {'confidence': confidence}
        filters_passed.append('hysteresis')
        
        # All filters passed - generate alert
        self.last_alert_time = time.time()
        self.last_alert_direction = direction
        self.total_alerts_sent += 1
        
        decision = Decision.ALERT_BULL if direction == "BULL" else Decision.ALERT_BEAR
        
        details = {
            'confidence': confidence,
            'confidence_raw': prob_up,
            'threshold_used': threshold_used,
            'filters_passed': filters_passed,
            'regime': regime,
        }
        
        return decision, "passed_all_filters", details
    
    def get_stats(self) -> Dict:
        """Get decision engine statistics."""
        return {
            'total_alerts_sent': self.total_alerts_sent,
            'last_alert_direction': self.last_alert_direction,
            'time_since_last_alert_minutes': (time.time() - self.last_alert_time) / 60 if self.last_alert_time > 0 else None,
        }
    
    def reset_cooldown(self):
        """Reset cooldown timer (for testing or manual override)."""
        self.last_alert_time = 0
        logger.info("Cooldown reset")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Testing DecisionEngine...")
    
    engine = DecisionEngine(
        bull_threshold=0.65,
        bear_threshold=0.65,
        min_body_pct=0.0010,
        min_range_pct=0.0012,
        min_vol_pctile=60,
        cooldown_minutes=10,
        hysteresis_margin=0.03,
    )
    
    # Test case 1: Strong bullish signal
    print("\nTest 1: Strong bullish signal")
    candle_info = {
        'body_pct': 0.0015,
        'range_pct': 0.0020,
        'volume_pctile': 75.0,
    }
    
    decision, reason, details = engine.decide(
        prob_up=0.78,
        prob_up_smoothed=0.75,
        candle_info=candle_info,
        regime="TREND"
    )
    
    print(f"Decision: {decision.value}")
    print(f"Reason: {reason}")
    print(f"Details: {details}")
    
    # Test case 2: Weak candle (should reject)
    print("\nTest 2: Weak candle")
    weak_candle = {
        'body_pct': 0.0005,  # Too weak
        'range_pct': 0.0020,
        'volume_pctile': 75.0,
    }
    
    decision, reason, details = engine.decide(
        prob_up=0.78,
        prob_up_smoothed=0.75,
        candle_info=weak_candle,
        regime="TREND"
    )
    
    print(f"Decision: {decision.value}")
    print(f"Reason: {reason}")
    
    # Test case 3: Cooldown (should reject)
    print("\nTest 3: Cooldown check")
    decision, reason, details = engine.decide(
        prob_up=0.78,
        prob_up_smoothed=0.75,
        candle_info=candle_info,
        regime="TREND"
    )
    
    print(f"Decision: {decision.value}")
    print(f"Reason: {reason}")
    
    # Get stats
    print(f"\nEngine stats: {engine.get_stats()}")
