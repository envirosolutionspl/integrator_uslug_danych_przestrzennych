import unittest
import random
from aio import add_service_v2


def create_test_class():
    class TestWebServicePlugin(unittest.TestCase):
        pass  

    
    for i in range(1, 26):  
        
        method_name = f'test_{i}'

        
        def test_method(self):
            zmienna = random.randint(0, 340)  

            
            result = add_service_v2(zmienna)

            
            self.assertEqual(result, 1, f"Expected {1}, but got {result}, zmienna: {zmienna}")

        
        setattr(TestWebServicePlugin, method_name, test_method)

    
    return TestWebServicePlugin


DynamicTestClass = create_test_class()


if __name__ == "__main__":
    unittest.main()

