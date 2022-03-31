I would like to thank Eric Foxely for creating the Nottingham
Database in machine readable form and making it available
in various forms on the Web. An early version of
the database was converted into abc music notation format
using a QBasic program written by Jay Glanville and
the abc files were posted on James Allwright's web site.

The converted files had numerous problems when I attempted
to convert them to MIDI files.  Over a period of
several months, I checked each of the tunes and made
necessary modifications so that they would be converted
properly into MIDI files. These changes fixed minor 
syntax errors and fixed missing or extra beats during 
repeats or transitions between parts as explained below.
In general I was conservative in my changes, and ignored
occasional warnings produced by abc2midi if the output MIDI
file was satisfactory.

Left repeats (|:) are usually missing in the notated
score. Most of the time abc2midi determines where to
assume the start of the repeat and merely issues a
polite reminder. In cases where abc2midi places them
incorrectly (due to anacrusis), I added the left
repeat to the score,

Some tunes are broken into parts, A, B, C etc. Abc2midi 
does not handle repeats correctly in this situation
but the P: field (eg. P: AABA) ensures that the parts
are played the correct number of times and in the correct
order. If I added the left repeat symbol, then the
part would be repeat 4 times instead of twice. 
I did not think this was intended, so I have left out
the missing |:. 

For many tunes, bar counts did not balance for some
repeats or transitions to the next part. I found it
necessary to indicate explicitly the bars to be
played during first and second repeat, so that the
rhythm would not sound broken during the repeat.

Abc2midi does not handle tied notes in chords the
way one would like. Thus
 |"G" [A2c2]- "C" [A2c2] |
should be notated as
 |"G" [A2-c2-] "C" [A2c2]|
if it is to be played as intended.

I changed the old chord representation +A2c2+ to the
accepted [A2c2]. 

Finally I made another pass through all the files
fixing all the "under full music lines" reported by yaps
(abc to postscript converter).

I hope these changes will allow more people to enjoy
this wonderful collection.

Seymour Shlien
Ottawa, Canada.

