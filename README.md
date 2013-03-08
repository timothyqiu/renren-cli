# Renren Command-line Interface

## 基本用法

    renren.py <命令> <参数...>

目前可用的命令：

* `login` 登录
* `logout` 登出
* `config` 配置相关，目前仅显示或清空配置
* `status` 状态相关
* `notify` 通知相关，目前仅显示所有通知

详细选项可使用 `-h` `--help` 查看。

## 状态相关

### 显示好友最新状态

    renren.py status                        # 显示第1页（每页5条）
    renren.py status --page 2               # 显示第2页
    renren.py status --page 3 --page-size 8 # 显示第3页，每页8条

### 状态详情

    renren.py status 2          # 显示第2条状态及回复
    renren.py status --page=2 2 # 显示第2页第2条状态及回复
    renren.py status 2 -c '123' # 回复第二条状态

## 已知问题

* 回复状态时指定的状态并非绝对位置，所以可能发串。
