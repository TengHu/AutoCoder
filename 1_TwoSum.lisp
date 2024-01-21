(defun two-sum (nums target)
  (let ((table (make-hash-table)))
    (dotimes (i (length nums))
      (let* ((num (elt nums i))
             (complement (- target num))
             (match (gethash complement table)))
        (if match
          (return (list match i))
          (setf (gethash num table) i))))))