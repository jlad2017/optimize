"""
Runs the main of all optimization scripts 
@authors: Jimmy Singh and Janice Lee 
@date: June 25th, 2019
"""
import lb_classic 
import lb_modified 
import adagrad 
import adagrad_lb_classic 
import adagrad_lb_modified 

def main():
    lb_classic.main() 
    lb_modified.main() 
    adagrad.main() 
    adagrad_lb_classic.main() 
    adagrad_lb_modified.main() 

if __name__ == '__main__':
    main()
