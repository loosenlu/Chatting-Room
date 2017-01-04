# Server
服务器主要使用IO复用。
服务器需要监控连接到该服务器上的所有用户套接字。
至于聊天室，实现上可以看成是对用户的分类，即同一个聊天室的用户属于同一类。
因此，主要包括两大类：
1. 用户信息
2. 聊天室信息
## User Abstract
1. client information
    + User ID
    + User name
2. socket: 套接字
---
## chat room abstract
1. 用户列表：每个房间需要记录该房间下的所有用户；
2. 
