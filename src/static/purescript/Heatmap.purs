module Heatmap where

import Data.Date (Date(), Year(..), Month(..), day, date)
import Data.Maybe
import Data.Enum
import Data.Map
import Debug.Trace
import Math

data CalendarParameters = CalendarParameters { earliest :: Date
                                             , latest :: Date
                                             , current :: Date
                                             , range :: Number -- number of months; must be at least one
                                             }

data Calendar = Map Date Number

-- calculate the days of the month
daysOfMonth :: Year -> Month -> Maybe Number
daysOfMonth y m =
  day <$> date y next 0
  where
  next = case succ m of
    Just(m) -> m
    Nothing -> December

main = print $ daysOfMonth 2015 February
