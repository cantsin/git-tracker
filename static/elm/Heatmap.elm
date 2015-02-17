module Heatmap where

import Text
import List
import Date (Date, toTime, fromTime)
import Time (Time, hour)
import Html (..)
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

-- actions that the user can do.
type Action = PreviousCalendar | NextCalendar | Display

daysToFloat: Int -> Time
daysToFloat days = (toFloat days) * 24 * hour

minDate: Date -> Date -> Date
minDate d1 d2 = if (toTime d1) < (toTime d2) then d1 else d2

maxDate: Date -> Date -> Date
maxDate d1 d2 = if (toTime d1) > (toTime d2) then d1 else d2

update: Action -> CalendarView -> CalendarView
update action cal =
    case action of
        PreviousCalendar ->
            let previous = toTime cal.starting + daysToFloat cal.days in
            { cal | starting <- maxDate cal.minDate (fromTime previous) }
        NextCalendar ->
            let next = toTime cal.starting - daysToFloat cal.days in
            { cal | starting <- minDate cal.maxDate (fromTime next) }

-- TODO: print out dates
-- TODO: add < and > buttons
view: CalendarView -> Html
view cal =
    div [] <| List.repeat cal.days <| div [] []

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
