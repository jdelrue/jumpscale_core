from Jumpscale import j

# import sys
import time

# import os
import psutil

JSBASE = j.application.JSBaseClass


class InfluxDumper(JSBASE):

    def __init__(self, testname, redis, server="localhost", port=8086, login="root", passwd="root"):
        JSBASE.__init__(self)
        self.redis = redis
        self.dbname = testname
        self.influxdb = j.clients.influxdb.get(
            host=server,
            port=port,
            username=login,
            password=passwd,
            database=None,
            ssl=False,
            verify_ssl=False,
            timeout=None,
            use_udp=False,
            udp_port=4444)

        try:
            self.influxdb.drop_database(testname)
        except BaseException:
            pass
        self.influxdb.create_database(testname)
        self.influxdb.switch_database(testname)

    def start(self):
        q = 'queues:stats'
        start = time.time()
        counter = 0
        data = ""
        while True:
            res = self.redis.lpop(q)
            while res is not None:
                counter += 1
                # print res
                measurement, key, tags, epoch, last, mavg, mmax, havg, hmax = res.split("|")
                # print "%s: %s:%s"%    (counter,key,last)
                # points.append(self.getPoint(key,timestamp=epoch,tags=None,last=last+"i",min_avg=mavg+"i",min_max=mmax+"i",h_avg=havg+"i",h_max=hmax+"i"))
                tags = "%s key:%s" % (tags.strip(), key)
                tags = tags.replace(" ", ",")
                tags = tags.replace(":", "=")
                last = int(last)
                # is BUG, but for now to be able to continue
                if last < 1000000:
                    data += "%s,%s value=%s %s\n" % (measurement, tags, last, epoch)
                else:
                    self.logger.info("SKIPPED:%s" % "%s,%s value=%s %s\n" % (measurement, tags, last, epoch))

                if counter > 100 or time.time() > start + 2:
                    start = time.time()
                    counter = 0
                    self.logger.debug(data)
                    j.clients.influxdb.postraw(data, host='localhost', port=8086,
                                               username='root', password='root', database=self.dbname)
                    # print "dump done to db:%s"%self.dbname
                    data = ""

                res = self.redis.lpop(q)

            time.sleep(1)
