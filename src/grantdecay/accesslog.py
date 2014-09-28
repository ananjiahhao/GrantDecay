"""Parse the access log export.

The access log export is a line-oriented text file. Blank lines and lines whose
first non-space character is ``#`` are ignored. The file begins with a required
header line that states the observation window as two ISO-8601 dates:

    window <start> <end>

Every subsequent record is one access event:

    <date> <principal> <permission>

