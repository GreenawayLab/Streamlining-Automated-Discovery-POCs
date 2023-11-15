"""
selection of colourblind friendly colours based on the colourblind pallete of seaborn
more information on setting seaborn aesthetics: https://seaborn.pydata.org/tutorial/aesthetics.html

run the next lines to see what the current colour scheme looks like
    import seaborn as sns
    sns.set(palette='colorblind')
    current_palette = sns.color_palette()
    sns.palplot(current_palette)
"""

_colour_1_hex: str = '#0173b2'  # dark blue
_colour_2_hex: str = '#de8f05'  # light orange
_colour_3_hex: str = '#029e73'  # dark green
_colour_4_hex: str = '#d55e00'  # dark orange
_colour_5_hex: str = '#cc78bc'  # dark pink
_colour_6_hex: str = '#ca9161'  # light brown
_colour_7_hex: str = '#fbafe4'  # light pink
_colour_8_hex: str = '#949494'  # grey
_colour_9_hex: str = '#ece133'  # yellow
_colour_10_hex: str = '#56b4e9'  # light blue
_colour_11_hex: str = '#b2df8a'  # light green, additional colour not in sns

_colour_1_rgb: tuple = (1, 115, 178)
_colour_2_rgb: tuple = (222, 143, 5)
_colour_3_rgb: tuple = (2, 158, 115)
_colour_4_rgb: tuple = (213, 94, 0)
_colour_5_rgb: tuple = (204, 120, 188)
_colour_6_rgb: tuple = (202, 145, 97)
_colour_7_rgb: tuple = (251, 175, 228)
_colour_8_rgb: tuple = (148, 148, 148)
_colour_9_rgb: tuple = (236, 225, 51)
_colour_10_rgb: tuple = (86, 180, 233)
_colour_11_rgb: tuple = (178, 223, 138)


_colour_1_bgr: tuple = (178, 115, 1)
_colour_2_bgr: tuple = (5, 143, 222)
_colour_3_bgr: tuple = (115, 158, 2)
_colour_4_bgr: tuple = (0, 94, 213)
_colour_5_bgr: tuple = (188, 120, 204)
_colour_6_bgr: tuple = (97, 145, 202)
_colour_7_bgr: tuple = (228, 175, 251)
_colour_8_bgr: tuple = (148, 148, 148)
_colour_9_bgr: tuple = (51, 225, 236)
_colour_10_bgr: tuple = (233, 180, 86)
_colour_11_bgr: tuple = (138, 223, 178)

