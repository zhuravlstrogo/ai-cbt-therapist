# ;0= @50;870F88 ">9 ?@>3@5AA"

## @E8B5:BC@0 <>4C;O

### A=>2=K5 :><?>=5=BK
1. **>4AG5B AB0B8AB8:8**
   - >;8G5AB2> 2K?>;=5==KE C?@06=5=89 87 exercises.xlsx
   - >;8G5AB2> 4=52=8:>2KE 70?8A59 87 diary.xlsx

2. **=0;87 G5@57 LLM (OpenRouter)**
   - !0<<0@8 ?> 4=52=8:0< M<>F89
   - !0<<0@8 ?> C?@06=5=8O<
   - 5@A>=0;878@>20==0O <>B828@CNI0O D@070

3. **=B5@D59A ?>;L7>20B5;O**
   - !B@C:BC@8@>20==K9 2K2>4 AB0B8AB8:8
   - @0A82>5 D>@<0B8@>20=85 @57C;LB0B>2
   - =>?:0 2>72@0B0 2 3;02=>5 <5=N

## !B@C:BC@0 40==KE

### 7 exercises.xlsx
- user_id
- exercise_name
- completed_date
- final_answers (8=A09BK, ?>;L70, B@C4=>AB8)
- steps_completed

### 7 diary.xlsx
- user_id
- date
- category (A8BC0F8O/<KA;8/M<>F88/?>2545=85)
- content
- distortion_type (5A;8 5ABL)
- belief_type (5A;8 5ABL)

## $C=:F88 <>4C;O

### `show_my_progress(bot, chat_id, user_id, username)`
;02=0O DC=:F8O >B>1@065=8O ?@>3@5AA0:
- 03@C605B 40==K5 87 Excel D09;>2
- $8;LB@C5B ?> user_id
- K7K205B DC=:F88 0=0;870
- $>@<8@C5B 8 >B?@02;O5B A>>1I5=85

### `count_completed_exercises(user_id)`
>4AG8BK205B :>;8G5AB2> 2K?>;=5==KE C?@06=5=89

### `count_diary_entries(user_id)`
>4AG8BK205B :>;8G5AB2> 70?8A59 2 4=52=8:5

### `generate_diary_summary(diary_data, user_problems)`
!>7405B A0<<0@8 ?> 4=52=8:0< G5@57 LLM:
- =0;878@C5B 48=0<8:C ?@>1;5<
- F5=8205B :>3=8B82=K5 8A:065=8O
- ?@545;O5B M<>F8>=0;L=CN >:@0A:C
- $>@<8@C5B ?A8E>;>38G5A:89 0=0;87

### `generate_exercise_summary(exercise_data)`
!>7405B A0<<0@8 ?> C?@06=5=8O< G5@57 LLM:
- =0;878@C5B ?>;=>BC >B25B>2
- >4AG8BK205B 8=A09BK
- F5=8205B MDD5:B82=>ABL

### `generate_motivational_phrase(user_data, diary_summary, exercise_summary)`
5=5@8@C5B ?5@A>=0;878@>20==CN <>B828@CNICN D@07C

## @><?BK 4;O LLM

### ;O 0=0;870 4=52=8:>2
```
"K >?KB=K9 ?A8E>;>3 ?> :>3=8B82=>-?>2545=G5A:>9 B5@0?88 A 15-;5B=8< AB065<.
@>0=0;878@C9 4=52=8:>2K5 70?8A8 :;85=B0:
- !B0@B>2K5 ?@>1;5<K: {problems}
- 0?8A8: {entries}

F5=8:
1. 8=0<8:C 87<5=5=89 (C;CGH5=85/CEC4H5=85/AB018;L=>)
2. '0AB>BC 8 8=B5=A82=>ABL :>3=8B82=KE 8A:065=89
3. -<>F8>=0;L=CN >:@0A:C 70?8A59
4. @>3@5AA ?> 70O2;5==K< ?@>1;5<0<

!D>@<C;8@C9 :@0B:>5 A0<<0@8 (3-4 ?@54;>65=8O), >B@060O 8 20;848@CO ?5@56820=8O :;85=B0, =>@<0;87CO 157 >15AF5=820=8O.
```

### ;O 0=0;870 C?@06=5=89
```
"K >?KB=K9 ?A8E>;>3 ?> :>3=8B82=>-?>2545=G5A:>9 B5@0?88 A 15-;5B=8< AB065<.
@>0=0;878@C9 2K?>;=5==K5 C?@06=5=8O:
- #?@06=5=8O: {exercises}
- B25BK =0 @5D;5:A8N: {final_answers}

F5=8:
1. ;C18=C ?@>@01>B:8 <0B5@80;0
2. >;8G5AB2> 8 :0G5AB2> 8=A09B>2
3. >2;5G5==>ABL 2 ?@>F5AA

!D>@<C;8@C9 :@0B:>5 A0<<0@8 (2-3 ?@54;>65=8O), ?>4G5@:820O A8;L=K5 AB>@>=K 8 4>AB865=8O.
```

### ;O <>B828@CNI59 D@07K
```
0 >A=>25 0=0;870 ?@>3@5AA0 :;85=B0 AD>@<C;8@C9 :>@>B:CN <>B828@CNICN D@07C (1 ?@54;>65=85).
$@070 4>;6=0 1KBL:
- 5@A>=0;878@>20==>9
- >78B82=>-@50;8AB8G=>9
- >445@6820NI59 40;L=59HCN @01>BC
```

## =B53@0F8O A universal_menu.py

 `handle_menu_callback()` 4;O action == 'my_progress':
```python
from my_progress import show_my_progress
await show_my_progress(bot, chat_id, user_id, username)
```

## 1@01>B:0 >H81>:
- @>25@:0 =0;8G8O D09;>2 Excel
- 1@01>B:0 ?CABKE 40==KE
- Fallback ?@8 >H81:0E LLM
- =D>@<0B82=K5 A>>1I5=8O >1 >H81:0E

## UI/UX
- A?>;L7>20=85 M<>478 4;O 287C0;870F88
- '5B:0O AB@C:BC@0 8=D>@<0F88
-  0745;5=85 A5:F89
- =>?:0 2>72@0B0 2 <5=N