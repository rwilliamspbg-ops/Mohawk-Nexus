package mohawksdk

import "math"

type FLState struct {
	Round  int
	Global *float64
	Updates []float64
}

func round6(v float64) float64 {
	return math.Round(v*1_000_000) / 1_000_000
}

func SwipScale(value float64) float64 {
	return round6(value * 1.5)
}

func FlApplyUpdate(state FLState, value float64) FLState {
	updates := make([]float64, 0, len(state.Updates)+1)
	updates = append(updates, state.Updates...)
	updates = append(updates, value)

	if len(updates) >= 2 {
		sum := 0.0
		for _, v := range updates {
			sum += v
		}
		avg := round6(sum / float64(len(updates)))
		return FLState{Round: state.Round + 1, Global: &avg, Updates: []float64{}}
	}

	norm := make([]float64, len(updates))
	for i, v := range updates {
		norm[i] = round6(v)
	}
	return FLState{Round: state.Round, Updates: norm}
}
