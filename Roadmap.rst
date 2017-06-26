3 service和task层的测试用例覆盖率不够
4 导入系统，单独模块导入问题
5 性能测试工具
6 gevent集成
11 thrift 安装集成
12 thrift工具功能细化
13 在存在fastweb进程启动期间，使用scrip等，会出现日志打印到之前的设置中
14 连接池上线控制
15 同步启动就rescue
16 web透传requestid到service层
17 service层的handler只加载对外开放的函数，其他不加载，加载service时可以使用thrift idl parse做些工作
19 log filter，某些场景需要过滤日志级别，比如脚本
load component + filter


♦︎ 连接池初始化后，中途mysql连接断开reconnect时增加超时时间，防止请求时长时间不返回
  ping机制也会等待很长时间(与tornado内部异常机制有关)

♦ 同步调用系统命令多进程性能问题，调研是否可以使用subprocess32来取代，或者使用长期打开的subprocess进行处理

♦ 各个模块测试场景覆盖，test框架完善

♦ 考虑集成Locust完成测试

♦ tox集成测试

♦ pytest替换unittest