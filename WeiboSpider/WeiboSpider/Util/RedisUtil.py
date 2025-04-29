import redis

class RedisQueueManager:
    def __init__(self):
        self.redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

    def add_task(self, task, priority):
        self.redis_client.zadd('WeiboUser:requests',{task: priority})

    def get_task(self):
        return self.redis_client.zpopmax('WeiboUser:requests')[0][0]

    def queue_length(self):
        return self.redis_client.llen('WeiboUser:requests')
    def clear_task(self):
        self.redis_client.flushdb()

if __name__ == '__main__':
    rqm = RedisQueueManager()