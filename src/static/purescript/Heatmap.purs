module Heatmap where

import Data.Date (Year(..), Month(..), day, date)
import Data.Maybe
import Data.Enum
import Debug.Trace
import Math

-- calculate the days of the month
daysOfMonth :: Year -> Month -> Maybe Number
daysOfMonth y m =
  day <$> date y next 0
  where
  next = case succ m of
    Just(m) -> m
    Nothing -> December

main = print $ daysOfMonth 2015 February
