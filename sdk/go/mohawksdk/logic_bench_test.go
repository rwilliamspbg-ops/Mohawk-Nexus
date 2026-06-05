package mohawksdk

import (
"testing"
)

func BenchmarkSwipScale(b *testing.B) {
value := 123.456789
b.ResetTimer()
for i := 0; i < b.N; i++ {
_ = SwipScale(value)
}
}

func BenchmarkFlApplyUpdate_Aggregate(b *testing.B) {
state := FLState{
Round:   5,
Updates: []float64{10.5, 20.3, 30.7},
}
value := 40.2
b.ResetTimer()
for i := 0; i < b.N; i++ {
_ = FlApplyUpdate(state, value)
}
}

func BenchmarkFlApplyUpdate_Buffer(b *testing.B) {
state := FLState{
Round:   0,
Updates: []float64{},
}
value := 15.75
b.ResetTimer()
for i := 0; i < b.N; i++ {
_ = FlApplyUpdate(state, value)
}
}

func BenchmarkFlApplyUpdate_SecondUpdate(b *testing.B) {
state := FLState{
Round:   1,
Updates: []float64{25.5},
}
value := 35.25
b.ResetTimer()
for i := 0; i < b.N; i++ {
_ = FlApplyUpdate(state, value)
}
}
