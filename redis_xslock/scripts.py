# coding: utf-8

__author__ = 'Junki Ishida'

from hashlib import sha1
from redis.exceptions import NoScriptError


class RedisScript:
    def __init__(self, script, numkeys=1, usesha=True):
        self.script = script.encode() if isinstance(script, str) else script
        self.hash = sha1(self.script).hexdigest()
        self.numkeys = numkeys
        self.usesha = usesha

    def execute(self, redis, *keys_and_args):
        if self.usesha:
            try:
                return redis.evalsha(self.hash, self.numkeys, *keys_and_args)
            except NoScriptError:
                return redis.eval(self.script, self.numkeys, *keys_and_args)
        else:
            return redis.eval(self.script, self.numkeys, *keys_and_args)


"""
simple mode scripts
"""
# ARGV[1]: expire
get_xlock_simple = RedisScript(b"""\
local value=redis.call('get',KEYS[1])
if not value or value=='0' then
    redis.call('set',KEYS[1],-1)
    redis.call('expire',KEYS[1],ARGV[1])
    return 0
end
return 1""")

# ARGV[1]: init on error
release_xlock_simple = RedisScript(b"""\
local value=redis.call('get',KEYS[1])
if value and value=='-1' then
    redis.call('del',KEYS[1])
    return 0
end
if ARGV[1]=='1' then redis.call('del',KEYS[1]) end
return 1""")

#ARGV[1]: expire
get_slock_simple = RedisScript(b"""\
local value=tonumber(redis.call('get',KEYS[1]))
if not value or value>=0 then
    redis.call('incr',KEYS[1])
    redis.call('expire',KEYS[1],ARGV[1])
    return 0
end
return 1""")

#ARGV[1]: init on error
release_slock_simple = RedisScript(b"""\
local value=tonumber(redis.call('get',KEYS[1]))
if value and value>0 then
    if value==1 then
        redis.call('del',KEYS[1])
    else
        redis.call('decr',KEYS[1])
    end
    return 0
end
if ARGV[1]=='1' then redis.call('del',KEYS[1]) end
return 1""")

"""
uuid mode scripts
"""
# ARGV[1]: euuid, ARGV[2]: expire
get_xlock_uuid = RedisScript(b"""\
local count=redis.call('scard',KEYS[1])
if count==0 then
    redis.call('sadd',KEYS[1],ARGV[1])
    redis.call('expire',KEYS[1],ARGV[2])
    return 0
end
return 1""")

#ARGV[1]: init on error, ARGV[2]: euuid
release_xlock_uuid = RedisScript(b"""\
local count=redis.call('scard',KEYS[1])
if count==1 and redis.call('sismember',KEYS[1],ARGV[2])==1 then
    redis.call('del',KEYS[1])
    return 0
end
if ARGV[1]=='1' then redis.call('del',KEYS[1]) end
return 1""")

# ARGV[1]: suuid, ARGV[2]: expire
get_slock_uuid = RedisScript(b"""\
local count,flag=redis.call('scard',KEYS[1]),false
if count==1 then
    local value=redis.call('smembers',KEYS[1])[1]
    if string.sub(value,1,1)=='s' then
        flag=true
    end
else
    flag=true
end
if flag then
    if count~=0 and redis.call('sismember',KEYS[1],ARGV[1])==1 then
        return 2
    end
    redis.call('sadd',KEYS[1],ARGV[1])
    redis.call('expire',KEYS[1],ARGV[2])
    return 0
end
return 1""")

#ARGV[1]: init on error, ARGV[2]: suuid
release_slock_uuid = RedisScript(b"""\
local count=redis.call('scard',KEYS[1])
if count==1 and redis.call('sismember',KEYS[1],ARGV[2])==1 then
    redis.call('del',KEYS[1])
    return 0
elseif count>0 then
    if redis.call('srem',KEYS[1],ARGV[2])==1 then
        return 0
    end
end
if ARGV[1]=='1' then redis.call('del',KEYS[1]) end
return 1""")

"""
safe_uuid mode scripts
"""
# ARGV[1]: uuid, ARGV[2]: current time, ARGV[3]: expire
get_xlock_safe_uuid = RedisScript(b"""\
local value,flag=redis.call('zrevrange',KEYS[1],0,1,'withscores'),false
if #value==0 then
    flag=true
elseif value[2]~='0' then
    local score,now=tonumber(value[2]),tonumber(ARGV[2])
    if score and now and score<now then
        redis.call('del',KEYS[1])
        flag=true
    end
end
if flag then
    redis.call('zadd',KEYS[1],0,ARGV[1])
    redis.call('expire',KEYS[1],ARGV[3])
    return 0
end
return 1""")

#ARGV[1]: init on error, ARGV[2]: uuid
release_xlock_safe_uuid = RedisScript(b"""\
local count=redis.call('zcard',KEYS[1])
if count==1 then
    local value=redis.call('zscore',KEYS[1],ARGV[2])
    if value=='0' then
        redis.call('del',KEYS[1])
        return 0
    end
end
if ARGV[1]=='1' then redis.call('del',KEYS[1]) end
return 1""")

# ARGV[1]: uuid, ARGV[2]: current time, ARGV[3]: expire
get_slock_safe_uuid = RedisScript(b"""\
local value=redis.call('zrange',KEYS[1],0,0,'withscores')
if #value==0 or value[2]~='0' then
    if redis.call('zscore',KEYS[1],ARGV[1]) then
        return 2
    end
    local expire=tonumber(ARGV[3])
    redis.call('zadd',KEYS[1],tonumber(ARGV[2])+expire,ARGV[1])
    redis.call('expire',KEYS[1],expire)
    return 0
end
return 1""")

#ARGV[1]: init on error, ARGV[2]: uuid
release_slock_safe_uuid = RedisScript(b"""\
local value=redis.call('zrange',KEYS[1],0,1,'withscores')
if #value~=0 and value[2]~='0' and redis.call('zscore',KEYS[1],ARGV[2]) then
    if #value==2 then
        redis.call('del',KEYS[1])
    else
        redis.call('zrem',KEYS[1],ARGV[2])
    end
    return 0
end
if ARGV[1]=='1' then redis.call('del',KEYS[1]) end
return 1""")
