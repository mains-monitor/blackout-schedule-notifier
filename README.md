# BSN - Blackout Schedule Notifier

This is a bash script and companion python app that:

- fetches blackout schedule from DTEK website every 30 minutes
- converts the schedule image into JSON representation
- if the schedule has changed - sends a Telegram message using Bot API

## Showcase

Here is what we get from the DTEK website.

<img src="docs/original.png">

Below the contour detection and grid recognition results achieved with ``python-opencv``. The ``pytesseract`` library helps to recognize the schedule date on the image.

<img src="docs/processed.png">

And here is a final JSON output:

    {
      "date_time": "29.11.2024",
      "blackouts": {
        "1": [
          {
            "start": "04:00",
            "end": "07:00"
          },
          {
            "start": "12:00",
            "end": "17:00"
          },
          {
            "start": "21:00",
            "end": "00:00"
          }
        ],
        "2": [
          {
            "start": "06:00",
            "end": "08:00"
          },
          {
            "start": "13:00",
            "end": "19:00"
          }
        ],
        "3": [
          {
            "start": "06:00",
            "end": "10:00"
          },
          {
            "start": "15:00",
            "end": "19:00"
          }
        ],
        "4": [
          {
            "start": "00:00",
            "end": "02:00"
          },
          {
            "start": "07:00",
            "end": "11:00"
          },
          {
            "start": "16:00",
            "end": "20:00"
          }
        ],
        "5": [
          {
            "start": "09:00",
            "end": "13:00"
          },
          {
            "start": "14:00",
            "end": "16:00"
          },
          {
            "start": "18:00",
            "end": "22:00"
          }
        ],
        "6": [
          {
            "start": "01:00",
            "end": "05:00"
          },
          {
            "start": "10:00",
            "end": "14:00"
          },
          {
            "start": "19:00",
            "end": "23:00"
          }
        ]
      }
    }



# Instructions

* Install https://github.com/tesseract-ocr/tesseract