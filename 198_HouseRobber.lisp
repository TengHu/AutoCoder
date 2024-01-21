(defun rob (nums)
  (cond
    ((null nums) 0)
    ((null (cdr nums)) (car nums))
    (t (let ((dp (list (car nums) (max (car nums) (cadr nums)))))
          (do ((i 2 (1+ i)))
              ((>= i (length nums)))
            (push (max (nth i nums) (+ (nth (1- i) dp) (car dp))) dp))
          (car dp)))))