module Heatmap where

import List
import Date (..)
import Html (..)
import Html.Events (..)
import Signal
import Util (..)

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

update: Action -> CalendarView -> CalendarView
update action cal =
    case action of
        PreviousCalendar ->
            let previous = toTime cal.starting - daysToFloat cal.days in
            { cal | starting <- maxDate cal.minDate (fromTime previous) }
        NextCalendar ->
            let next = toTime cal.starting + daysToFloat cal.days in
            { cal | starting <- minDate cal.maxDate (fromTime next) }

view: CalendarView -> Html
view cal =
    let clickPrev = button [ onClick (Signal.send actionChannel PreviousCalendar) ] [ text "<" ]
        clickNext = button [ onClick (Signal.send actionChannel NextCalendar) ] [ text ">" ]
        header = text <| timeToString <| toTime cal.starting
        start = toTime cal.starting
        calendar = List.map (\n -> div [] [ text <| timeToString (start + (toFloat n) * oneday) ]) [1..cal.days] in
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
