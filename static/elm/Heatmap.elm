module Heatmap where

import Text
import List
import Time
import Date (..)
import Html (..)
import Html.Events (..)
import Signal

port appMinDate: Float
port appMaxDate: Float
port appToday: Float
-- TODO json data to process

-- our calendar model.
type alias CalendarView = { minDate: Date
                          , maxDate: Date
                          , starting: Date
                          , days: Int
                          }

-- drawing options.
-- TODO

-- actions that can be applied to our model.
type Action = PreviousCalendar | NextCalendar | Display

oneday: Time.Time
oneday = 24 * Time.hour

daysToFloat: Int -> Time.Time
daysToFloat days = (toFloat days) * oneday

minDate: Date -> Date -> Date
minDate d1 d2 = if (toTime d1) < (toTime d2) then d1 else d2

maxDate: Date -> Date -> Date
maxDate d1 d2 = if (toTime d1) > (toTime d2) then d1 else d2

update: Action -> CalendarView -> CalendarView
update action cal =
    case action of
        PreviousCalendar ->
            let previous = toTime cal.starting - daysToFloat cal.days in
            { cal | starting <- maxDate cal.minDate (fromTime previous) }
        NextCalendar ->
            let next = toTime cal.starting + daysToFloat cal.days in
            { cal | starting <- minDate cal.maxDate (fromTime next) }

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

printDate: Float -> Html
printDate when =
    let date = fromTime when
        m = month date
        d = day date
        y = year date in
    text <| monthToString m ++ "/" ++ toString d ++ "/" ++ toString y

view: CalendarView -> Html
view cal =
    let clickPrev = button [ onClick (Signal.send actionChannel PreviousCalendar) ] [ text "<" ]
        clickNext = button [ onClick (Signal.send actionChannel NextCalendar) ] [ text ">" ]
        header = printDate <| toTime cal.starting
        start = toTime cal.starting
        calendar = List.map (\n -> div [] [ printDate (start + (toFloat n) * oneday) ]) [1..cal.days] in
    div [] <| header :: clickPrev :: clickNext :: calendar

model: Signal CalendarView
model =
    let cal = { minDate = fromTime appMinDate
              , maxDate = fromTime appMaxDate
              , starting = fromTime appToday
              , days = 30 } in
    Signal.foldp update cal (Signal.subscribe actionChannel)

actionChannel: Signal.Channel Action
actionChannel = Signal.channel Display

main : Signal Html
main =
    Signal.map view model
