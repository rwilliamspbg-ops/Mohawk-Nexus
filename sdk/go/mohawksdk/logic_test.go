package mohawksdk

import (
	"encoding/json"
	"os"
	"path/filepath"
	"runtime"
	"testing"
)

type fixture struct {
	Cases []struct {
		Name     string                 `json:"name"`
		Kind     string                 `json:"kind"`
		Input    map[string]interface{} `json:"input"`
		Expected map[string]interface{} `json:"expected"`
	} `json:"cases"`
}

func loadFixture(t *testing.T) fixture {
	_, file, _, ok := runtime.Caller(0)
	if !ok {
		t.Fatal("cannot get caller path")
	}
	path := filepath.Clean(filepath.Join(filepath.Dir(file), "..", "..", "fixtures", "conformance", "cases.json"))
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("read fixture: %v", err)
	}
	var f fixture
	if err := json.Unmarshal(raw, &f); err != nil {
		t.Fatalf("parse fixture: %v", err)
	}
	return f
}

func TestConformanceCases(t *testing.T) {
	f := loadFixture(t)
	for _, c := range f.Cases {
		t.Run(c.Name, func(t *testing.T) {
			switch c.Kind {
			case "swip_scale":
				v := c.Input["value"].(float64)
				got := SwipScale(v)
				expected := c.Expected["result"].(float64)
				if got != expected {
					t.Fatalf("got %v expected %v", got, expected)
				}
			case "fl_apply_update":
				stateMap := c.Input["state"].(map[string]interface{})
				round := int(stateMap["round"].(float64))
				updatesAny, _ := stateMap["updates"].([]interface{})
				updates := make([]float64, 0, len(updatesAny))
				for _, u := range updatesAny {
					updates = append(updates, u.(float64))
				}
				val := c.Input["value"].(float64)
				got := FlApplyUpdate(FLState{Round: round, Updates: updates}, val)
				expectedRound := int(c.Expected["round"].(float64))
				if got.Round != expectedRound {
					t.Fatalf("round got %v expected %v", got.Round, expectedRound)
				}
				if expectedGlobal, ok := c.Expected["global"]; ok {
					if got.Global == nil || *got.Global != expectedGlobal.(float64) {
						t.Fatalf("global got %v expected %v", got.Global, expectedGlobal)
					}
				}
				expectedUpdates, ok := c.Expected["updates"].([]interface{})
				if !ok {
					expectedUpdates = []interface{}{}
				}
				if len(got.Updates) != len(expectedUpdates) {
					t.Fatalf("updates len got %v expected %v", len(got.Updates), len(expectedUpdates))
				}
				for i, v := range expectedUpdates {
					if got.Updates[i] != v.(float64) {
						t.Fatalf("update[%d] got %v expected %v", i, got.Updates[i], v)
					}
				}
			default:
				t.Fatalf("unknown case kind %s", c.Kind)
			}
		})
	}
}

func FuzzFlApplyUpdate(f *testing.F) {
	f.Add(0, int64(0), 0.0)
	f.Add(5, int64(3), 40.2)
	f.Add(1, int64(1), 35.25)
	f.Add(0, int64(0), -999.999)
	f.Add(100, int64(3), 0.5)

	f.Fuzz(func(t *testing.T, round int, numUpdates int64, value float64) {
		if numUpdates < 0 || numUpdates > 1000 {
			return
		}
		
		updates := make([]float64, numUpdates)
		for i := range updates {
			updates[i] = float64(i) * 0.1
		}
		
		state := FLState{Round: round, Updates: updates}
		result := FlApplyUpdate(state, value)

		if result.Round < round {
			t.Errorf("round decreased: got %d, expected >= %d", result.Round, round)
		}

		if result.Global != nil && (*result.Global < -1e15 || *result.Global > 1e15) {
			t.Errorf("global value out of reasonable range: %v", *result.Global)
		}

		for i, v := range result.Updates {
			if v < -1e15 || v > 1e15 {
				t.Errorf("update[%d] out of reasonable range: %v", i, v)
			}
		}
	})
}

func FuzzSwipScale(f *testing.F) {
	f.Add(0.0)
	f.Add(123.456789)
	f.Add(-999.999)
	f.Add(1e-10)
	f.Add(1e6)

	f.Fuzz(func(t *testing.T, value float64) {
		if value < -1e9 || value > 1e9 {
			return
		}
		
		result := SwipScale(value)

		expectedScale := value * 1.5
		tolerance := 2e-6
		if result < expectedScale-tolerance || result > expectedScale+tolerance {
			diff := result - expectedScale
			if diff < -tolerance || diff > tolerance {
				t.Errorf("SwipScale(%v) = %v, expected ~%v (diff: %v)", value, result, expectedScale, diff)
			}
		}
	})
}
