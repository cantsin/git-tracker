import Text
import List
import Date (Date, toTime, fromTime)
import Time (Time, hour)
import Html (..)

-- our calendar model.
type alias Calendar = { starting: Date
                      , days: Int }

-- drawing options.
-- TODO

-- actions that the user can do.
type Action = ChooseCalendarDay | PreviousCalendar | NextCalendar

daysToFloat: Int -> Time
daysToFloat days = (toFloat days) * 24 * hour

update: Action -> Calendar -> Calendar
update action cal =
    case action of
        ChooseCalendarDay -> cal
        PreviousCalendar ->
            let previous = toTime cal.starting + daysToFloat cal.days in
            { cal | starting <- fromTime previous }
        NextCalendar ->
            let next = toTime cal.starting - daysToFloat cal.days in
            { cal | starting <- fromTime next }

view: Calendar -> Html
view cal =
    div [] <| List.repeat cal.days <| div [] []

main = Text.plainText "Hello World"
