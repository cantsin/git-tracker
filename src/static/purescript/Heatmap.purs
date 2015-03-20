module Heatmap where

import Debug.Trace
import Math

diagonal :: Number -> Number -> Number
diagonal w h = sqrt (w * w + h * h)

main = print $ diagonal 3 4
