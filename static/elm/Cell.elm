module Cell where

import Date (..)
import Html (..)

type alias CellData = { date: Date
                      , count: Int
                      }

-- drawing options.
port appcellSize: Int
port appcellPadding: Int
port appcellRadius: Int

type alias CellOptions = { cellSize: Int
                         , cellPadding: Int
                         , cellRadius: Int
                         }

-- draw a cell.
view: CellData -> CellOptions -> Html
view = undefined

model: Signal CellData
model =
    let options = { cellSize = 10
                  , cellPadding = 2
                  , cellRadius = 0 } in

    Signal.foldp update cal (Signal.subscribe actionChannel)
