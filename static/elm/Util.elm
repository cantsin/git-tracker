{- various utility functions. -}
module Util where

import Time
import Date (..)

oneday: Time.Time
oneday = 24 * Time.hour

daysToFloat: Int -> Time.Time
daysToFloat days = (toFloat days) * oneday

minDate: Date -> Date -> Date
minDate d1 d2 = if (toTime d1) < (toTime d2) then d1 else d2

maxDate: Date -> Date -> Date
maxDate d1 d2 = if (toTime d1) > (toTime d2) then d1 else d2

-- mm/dd/YYYY
monthToString: Month -> String
monthToString m =
    case m of
      Jan -> "01"
      Feb -> "02"
      Mar -> "03"
      Apr -> "04"
      May -> "05"
      Jun -> "06"
      Jul -> "07"
      Aug -> "08"
      Sep -> "09"
      Oct -> "10"
      Nov -> "11"
      Dec -> "12"

timeToString: Float -> String
timeToString when =
    let date = fromTime when
        m = month date
        d = day date
        y = year date in
    monthToString m ++ "/" ++ toString d ++ "/" ++ toString y
