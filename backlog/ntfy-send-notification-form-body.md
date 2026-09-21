# ntfy_tools: send_notification delivers a form-encoded body as the message text

    found:  2026-09-21
    status: open
    verify: grep -n 'data={"message"' src/readable_utils/ntfy_tools.py

`send_notification` posts `data={"message": message}`, so requests sends a
`application/x-www-form-urlencoded` body. ntfy takes the whole POST body as
the message, so every subscriber sees the url-encoded form string instead of
the text.

## Evidence

Polled from the house_power topic on 2026-09-21 after the raspberrypi3a UPS
notifier fired a power-restored event (`GET /house_power/json?poll=1&since=1h`):

    {"id":"2DFKUXDNRHJ1","time":1790021474,"expires":1790064674,"event":"message","topic":"house_power","message":"message=Power+event+detected%3A+power-restored.+Initiating+shutdown+sequence+stage+1."}

## fix

In `src/readable_utils/ntfy_tools.py` post the text as the raw body:

    response = requests.post(topic_url, auth=(NTFY_USERNAME, NTFY_PASSWORD), data=message.encode("utf-8"))

Then tag a release and bump the pin in every repo that depends on
readable-utils with the `[ntfy]` extra (Assistant on the pis is the one that
sends the UPS events).

## blast radius

Every caller of `send_notification` starts receiving plain text instead of
the `message=...` string. Nothing parses the old form, so none.

## not doing yet

Found while restoring UPS notifications on the pis; the change needs a
readable-utils tag and a pin bump per consumer, which is a separate commit
cycle from the pi fix.
