# TKB_Bot

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Requirements
Use the package manager pip to install dependencies
* Python>=3.0 (Test on 3.8.2)
* pip(or you can use other package manager that you prefer)
* requests==2.24.0
* selenium==3.141.0

```
pip install -r requirements.txt
```

### Installing
依照下列格式，修改 config.ini 中之參數欄位
```python
st_id         = 'A123456789'       # 帳號
st_pwd        = 'Ab123456'         # 密碼
select_class  = 2                  # 欲上課課程
#-------以下擇一填寫-------
snap_up       = True               # 自動搶課模式
select_date   = '2020-08-12'       # 欲上課日期
#-------------------------
select_branch = 'WA'               # 嘉義場==WA
session_time  = ['1','2','3']      # 上課場次
dev           = False              # 是否在開發階段
EnterPoint    = 'https://bookseat.tkblearning.com.tw/book-seat/student/login/logout' #選課網址
```

* `select_class` 按照網頁上的課程順序，由1開始(只能選一堂)，可以隨便選因為選上可以修改。e.g.資結==1 計概==2 英文==3
* `snap_up` 若為 `True` 則忽略下列指定欲上課日期，直接搶今天起七天後的課 `False`：搶下列指定欲上課日期的課
* `select_date` 指定欲上課日期
* `select_branch` 選擇上課地點(嘉義場==WA)
* `session_time` 選擇上課場次(TKB規定最多3個)
* `dev` 不須更動，若更改為`True`則不會送出選課
* `EnterPoint` 不須更動



## Running the tests

```
python TKB_Bot.py
```
