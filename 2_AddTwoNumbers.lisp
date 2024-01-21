(defun add-two-numbers (l1 l2)
  (let ((carry 0) (res nil))
    (loop for x in (mapcar #'cons l1 l2) do
         (let* ((sum (+ (car x) (cdr x) carry))
                (node (% sum 10)))
           (push node res)
           (setf carry (floor sum 10))))
    (if (= carry 1) (push 1 res))
    (nreverse res)))