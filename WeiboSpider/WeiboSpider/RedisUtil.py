import redis


class RedisQueueManager:

    redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

    @classmethod
    def add_task(cls, task, priority):
        cls.redis_client.zadd('WeiboUser:requests', {task: priority})

    @classmethod
    def get_task(cls):
        return cls.redis_client.zpopmax('WeiboUser:requests')[0][0]

    @classmethod
    def queue_length(cls):
        return cls.redis_client.llen('WeiboUser:requests')

    @classmethod
    def clear_task(cls):
        cls.redis_client.flushdb()

RedisQueueManager.clear_task()