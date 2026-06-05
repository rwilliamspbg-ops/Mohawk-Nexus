package mohawksdk

const round6Factor = 1_000_000

type FLState struct {
	Round   int
	Global  *float64
	Updates []float64
}

func round6(v float64) float64 {
	return float64(int64(v*round6Factor+0.5)) / round6Factor
}

func SwipScale(value float64) float64 {
	return round6(value * 1.5)
}

func FlApplyUpdate(state FLState, value float64) FLState {
	numUpdates := len(state.Updates) + 1

	if numUpdates >= 2 {
		sum := value
		for _, v := range state.Updates {
			sum += v
		}
		avg := round6(sum / float64(numUpdates))
		return FLState{Round: state.Round + 1, Global: &avg, Updates: nil}
	}

	return FLState{Round: state.Round, Updates: []float64{round6(value)}}
}
