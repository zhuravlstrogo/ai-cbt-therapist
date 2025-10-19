# Check-in Module Plan

## 17>@ DC=:F8>=0;L=>AB8
>4C;L 565=545;L=>9 >F5=:8 ?@>3@5AA0, :>B>@K9 02B><0B8G5A:8 70?CA:05BAO @07 2 =545;N >B 40BK ?5@2>3> /start 8 <>65B 1KBL 2K720= 2@CG=CN G5@57 :=>?:C "=È F5=8BL ?@>3@5AA" 2 3;02=>< <5=N.

## @E8B5:BC@0

### 1. !B@C:BC@0 40==KE (check-in.xlsx)
>;>=:8:
- User ID
- Username
- User Name (8<O ?>;L7>20B5;O)
- Check-in Date
- Days Since Start (4=59 A =0G0;0 B5@0?88)
- Question 1 Response (0: 45;0?)
- Question 2 Response (0: A51O GC2AB2C5HL?)
- Problems Ratings (JSON: {"problem_name": rating})
- Goal Progress (0-10)
- Weekly Summary (LLM-generated)
- Crisis Detected (boolean)
- Crisis Type (if detected)

### 2. A=>2=K5 DC=:F88

#### =8F80;870F8O 8 ?;0=8@>20=85
- `init_check_in_scheduler(bot)` - 70?CA: ?;0=8@>2I8:0 565=545;L=KE ?@>25@>:
- `get_next_check_in_date(user_id)` - @0AG5B A;54CNI59 40BK check-in
- `should_do_check_in(user_id)` - ?@>25@:0, =C65= ;8 check-in A59G0A

#### @>F5AA check-in
- `start_check_in(bot, chat_id, user_id, username)` - =0G0;> ?@>F5AA0
- `show_question_1(bot, chat_id, user_id)` - "0: C B51O 45;0?"
- `show_question_2(bot, chat_id, user_id)` - "0: A51O GC2AB2C5HL?"
- `show_problem_ratings(bot, chat_id, user_id)` - >F5=:0 :064>9 ?@>1;5<K
- `show_goal_progress(bot, chat_id, user_id)` - ?@>3@5AA : F5;8 (0-10)

#### =0;87 8 A0<<0@8
- `generate_weekly_summary(user_id, responses)` - LLM 0=0;87 ?@>3@5AA0
- `check_crisis_indicators(responses)` - ?@>25@:0 :@878A=KE 8=48:0B>@>2
- `show_crisis_support(bot, chat_id, user_id)` - ?>:07 :@878A=>9 ?>445@6:8

#### !>E@0=5=85 40==KE
- `save_check_in_results(user_id, username, responses)` - A>E@0=5=85 2 Excel

### 3. !>AB>O=8O ?>;L7>20B5;O
```python
user_checkin_states = {
    user_id: {
        'step': int,  # 1-4 (2>?@>AK) + 5 (A0<<0@8)
        'responses': {
            'q1_response': str,
            'q2_response': str,
            'problem_ratings': dict,
            'goal_progress': int
        },
        'current_problem_idx': int,
        'start_date': datetime
    }
}
```

### 4. Workflow

#### 2B><0B8G5A:89 70?CA: (@07 2 =545;N)
```
Scheduler ?@>25@O5B 2A5E ?>;L7>20B5;59
    “
A;8 ?@>H;0 =545;O A ?>A;54=53> check-in
    “
B?@028BL ?@825BAB285 A 20@80F859
    “
0G0BL ?@>F5AA check-in
```

####  CG=>9 70?CA: (:=>?:0 2 <5=N)
```
>;L7>20B5;L =068<05B "=È F5=8BL ?@>3@5AA"
    “
@>25@:0: ?@>H;> ;8 E>BO 1K 3 4=O A ?>A;54=53>?
    “
0: 0G0BL check-in | 5B: >:070BL ?>A;54=89 ?@>3@5AA
```

#### @>F5AA check-in
```
1. "@825B! 0: C B51O 45;0?" ’ !2>1>4=K9 >B25B
    “
2. "0: BK A59G0A A51O GC2AB2C5HL?" ’ !2>1>4=K9 >B25B
    “
3. F5=:0 :064>9 ?@>1;5<K (0-3) ’ > >G5@548 :0: 2 goal.py
    “
4. "0A:>;L:> ?@>428=C;AO : F5;8?" ’ =>?:8 0-10
    “
5. 5=5@0F8O A0<<0@8 G5@57 LLM
    “
6. @>25@:0 :@878A=KE 8=48:0B>@>2
    “
7. >:07 @57C;LB0B>2 8;8 :@878A=>9 ?>445@6:8
```

### 5. LLM ?@><?BK

#### !0<<0@8 ?@>3@5AA0
```python
system_prompt = """"K >?KB=K9 ?A8E>B5@0?52B ". @>0=0;878@C9 =545;L=K9 ?@>3@5AA :;85=B0.

:;NG8:
1. &8B0BK 8=A09B>2 87 C?@06=5=89 (5A;8 5ABL)
2. >445@6820NICN 48=0<8:C
3. O3:85 =01;N45=8O ?> ?0BB5@=0<
4. >B828@CNI55 ?@54;>65=85 A;54CNI53> H030

">=: B5?;K9, ?>445@6820NI89, ?@>D5AA8>=0;L=K9."""

user_prompt = f"""
<O: {user_name}
B25BK =0 check-in: {responses}
=A09BK 87 C?@06=5=89 70 =545;N: {insights}
8=0<8:0 >F5=>: ?@>1;5<: {problem_dynamics}
"""
```

#### @>25@:0 :@878A=KE 8=48:0B>@>2
```python
system_prompt = """"K >?KB=K9 :@878A=K9 ?A8E>;>3. @>25@L B5:AB =0 =0;8G85 :@878A=KE 8=48:0B>@>2:
- !C8F840;L=K5 <KA;8/=0<5@5=8O
- @87=0:8 ?A8E>70
- K@065==0O 45?5@A>=0;870F8O/45@50;870F8O
- !5;D-E0@<
- 028A8<>AB8 
- 0=80:0;L=K5 A>AB>O=8O

B25BL JSON: {"crisis_detected": bool, "crisis_type": str or null, "confidence": float}"""
```

### 6. 0@80F88 ?@825BAB289
```python
GREETINGS = [
    "@825B! 0: C B51O 45;0?",
    "@825B! 0: B2>8 45;0 =0 MB>9 =545;5?",
    "@825B! 0: ?@>H;0 B2>O =545;O?",
    "@825B! 0: BK A51O GC2AB2C5HL A53>4=O?",
    "@825B!  04(0) B51O 2845BL! 0: 45;0?"
]
```

### 7. =B53@0F8O A 4@C38<8 <>4C;O<8

#### >;CG5=85 40==KE 87:
- `greeting.user_states` - 8<O, 40B0 AB0@B0, ?@>1;5<K
- `exercises.xlsx` - 8=A09BK 87 C?@06=5=89 70 =545;N
- `diary.xlsx` - 70?8A8 4=52=8:0 70 =545;N

#### Callback handlers:
- `checkin:start` - =0G0BL check-in
- `checkin:q1_next` - ?5@5E>4 : 2>?@>AC 2
- `checkin:q2_next` - ?5@5E>4 : >F5=:5 ?@>1;5<
- `checkin:rate_problem:{idx}:{rating}` - >F5=:0 ?@>1;5<K
- `checkin:goal_progress:{value}` - ?@>3@5AA : F5;8
- `checkin:crisis_help` - ?>:070BL ?><>IL
- `checkin:crisis_later` - =0?><=8BL ?>765
- `checkin:skip` - ?@>?CAB8BL (5A;8 =5402=> 1K;)

### 8. A>15==>AB8 @50;870F88

1. **A8=E@>==>ABL**: A5 >?5@0F88 async/await
2. **1@01>B:0 >H81>:**: Try-except 1;>:8 A fallback
3. **MH8@>20=85**: LLM >B25BK :MH8@CNBAO =0 24 G0A0
4. **57>?0A=>ABL**: 5<54;5==K9 >B25B =0 callback 4;O ?@54>B2@0I5=8O timeout
5. **5@A8AB5=B=>ABL**: !>E@0=5=85 ?@><56CB>G=KE @57C;LB0B>2

## >?@>AK 4;O CB>G=5=8O

1. **;0=8@>2I8:**: A?>;L7>20BL APScheduler 8;8 ?@>AB>9 asyncio.create_task A while loop?
2. **'0AB>B0**: !B@>3> @07 2 =545;N 8;8 @07@5H8BL G0I5 G5@57 :=>?:C?
3. **@878A**: 2B><0B8G5A:8 C254><;OBL A?5F80;8AB0 8;8 B>;L:> ?>:07K20BL :>=B0:BK?
4. **AB>@8O**: >:07K20BL 3@0D8: ?@>3@5AA0 8;8 B>;L:> B5:CI55 A>AB>O=85?
5. **0?><8=0=8O**: B?@02;OBL =0?><8=0=8O 5A;8 ?>;L7>20B5;L =5 >B25G05B?