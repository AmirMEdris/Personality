import http.client,json,threading,unittest
from personality.server import Handler,ThreadingHTTPServer,ROOT
class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler);cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join()
    def request(self,method,path,body=None,headers=None):
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5);c.request(method,path,body,headers or {});r=c.getresponse();status=r.status;data=r.read();c.close();return status,data
    def test_routes_and_privacy(self):
        self.assertEqual(self.request('GET','/')[0],200)
        for path in ['/data/drug_consumption.data','/../config/target.json','/api/answers']:
            self.assertEqual(self.request('GET',path)[0],404)
        self.assertEqual(self.request('GET','/',headers={'Host':'evil.example'})[0],403)
    def test_predictions_and_origin(self):
        example=json.loads((ROOT/'artifacts/examples.json').read_text())[0]
        body=json.dumps({'features':example['features'],'measurement':'uci373_quantified'})
        self.assertEqual(self.request('POST','/api/predict',body)[0],200)
        self.assertEqual(self.request('POST','/api/predict',body,{'Origin':'https://evil.example'})[0],403)
        self.assertEqual(self.request('POST','/api/predict','[]')[0],400)
        self.assertEqual(self.request('POST','/api/predict',body.replace('uci373_quantified','ipip'))[0],400)
if __name__=='__main__':unittest.main()
