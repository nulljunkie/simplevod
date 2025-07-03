from typing import List, NamedTuple, Optional
from domain.interfaces import TimestampSelector

class TimestampCandidate(NamedTuple):
    timestamp: float
    index: int

class OptimalTimestampSelector(TimestampSelector):
    
    def select_optimal_timestamps(
        self, 
        keyframes: List[float], 
        min_period: float, 
        max_period: float
    ) -> List[float]:
        if not keyframes:
            return []

        sorted_frames = self._prepare_keyframes(keyframes)
        if len(sorted_frames) == 1:
            return sorted_frames

        return self._select_using_greedy_approach(sorted_frames, min_period, max_period)

    def _prepare_keyframes(self, keyframes: List[float]) -> List[float]:
        return sorted(set(keyframes))

    def _select_using_greedy_approach(
        self, 
        sorted_frames: List[float], 
        min_period: float, 
        max_period: float
    ) -> List[float]:
        selected = [sorted_frames[0]]
        last_selected = sorted_frames[0]
        
        i = 1
        while i < len(sorted_frames):
            candidates = self._find_candidates_in_window(
                sorted_frames, i, last_selected, min_period, max_period
            )
            
            if candidates:
                best = self._select_best_candidate(candidates)
                selected.append(best.timestamp)
                last_selected = best.timestamp
                i = best.index + 1
            else:
                next_timestamp = self._handle_no_candidates(
                    sorted_frames, i, last_selected, min_period, max_period
                )
                if next_timestamp:
                    selected.append(next_timestamp.timestamp)
                    last_selected = next_timestamp.timestamp
                    i = next_timestamp.index + 1 if next_timestamp.index >= 0 else i
                else:
                    synthetic = last_selected + max_period
                    selected.append(synthetic)
                    last_selected = synthetic
                    i += 1

        self._add_final_timestamp_if_needed(selected, sorted_frames, min_period)
        return selected

    def _find_candidates_in_window(
        self, 
        frames: List[float], 
        start_idx: int, 
        last_selected: float, 
        min_period: float, 
        max_period: float
    ) -> List[TimestampCandidate]:
        candidates = []
        for i in range(start_idx, len(frames)):
            gap = frames[i] - last_selected
            if gap > max_period:
                break
            if gap >= min_period:
                candidates.append(TimestampCandidate(frames[i], i))
        return candidates

    def _select_best_candidate(self, candidates: List[TimestampCandidate]) -> TimestampCandidate:
        return candidates[-1]

    def _handle_no_candidates(
        self, 
        frames: List[float], 
        start_idx: int, 
        last_selected: float, 
        min_period: float, 
        max_period: float
    ) -> Optional[TimestampCandidate]:
        next_natural = self._find_next_natural_after_window(frames, start_idx, last_selected, max_period)
        
        if next_natural and next_natural.timestamp - last_selected >= min_period:
            return next_natural
        return None

    def _find_next_natural_after_window(
        self, 
        frames: List[float], 
        start_idx: int, 
        last_selected: float, 
        max_period: float
    ) -> Optional[TimestampCandidate]:
        for i in range(start_idx, len(frames)):
            if frames[i] - last_selected > max_period:
                return TimestampCandidate(frames[i], i)
        return None

    def _add_final_timestamp_if_needed(
        self, 
        selected: List[float], 
        sorted_frames: List[float], 
        min_period: float
    ) -> None:
        last_frame = sorted_frames[-1]
        if (last_frame != selected[-1] and 
            last_frame - selected[-1] >= min_period):
            selected.append(last_frame)