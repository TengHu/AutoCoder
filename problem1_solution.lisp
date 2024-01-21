(defun solve-problem1 (arr) 
  (cond 
    ((null arr) nil)
    (t
      (let ((max-val (apply 'max arr))
            (min-val (apply 'min arr)))
        (- max-val min-val)))))