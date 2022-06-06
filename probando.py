
import os

from transcription import (
    SUBTITLE_LOCAL_DIRECTORY, translate_lines
)

lines_to_let_equal = list()
lines_to_translate = list()



f = open(os.path.join(SUBTITLE_LOCAL_DIRECTORY, "videoplayback.vtt"), "r", encoding="utf8")
cont = 0
cont_before_vtt = 2
for line in f:
    line = line.replace("\n", "")

    if cont < cont_before_vtt:
        lines_to_let_equal.append(line)
        cont += 1
        continue

    if cont % 4 == 0:
        lines_to_translate.append(line)
    else:
        lines_to_let_equal.append(line)
    cont += 1
f.close()

# Translation process

text_translated = translate_lines(lines_to_translate, "es-ES", "en-GB")

print(text_translated)