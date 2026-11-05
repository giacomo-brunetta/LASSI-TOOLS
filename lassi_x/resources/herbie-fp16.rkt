#lang herbie/platform

;; Experimental IEEE binary16/binary32 arithmetic search model. Costs are
;; dimensionless heuristics, not accelerator measurements. No FMA, branches,
;; transcendentals, reductions, flush-to-zero, or hardware-specific fusion.
(require math/bigfloat
         math/flonum)
(provide half-round
         half->ordinal
         ordinal->half)

(define (exponent q)
  (define e (- (integer-length (numerator q)) (integer-length (denominator q))))
  (if (< q (expt 2 e))
      (sub1 e)
      e))

(define (half-round x)
  (cond
    [(or (nan? x) (infinite? x)) x]
    [(zero? x) (if (exact? x) 0.0 x)]
    [else
     (define sign (if (negative? x) -1.0 1.0))
     (define q (abs (inexact->exact x)))
     (cond
       [(>= q 65520) (* sign +inf.0)]
       [else
        (define spacing (expt 2 (max -24 (- (exponent q) 10))))
        (* sign (exact->inexact (* spacing (round (/ q spacing)))))])]))

(define (ordinal->half ordinal)
  (define sign (if (negative? ordinal) -1.0 1.0))
  (define bits (abs ordinal))
  (define e (bitwise-bit-field bits 10 15))
  (define fraction (bitwise-and bits #x3ff))
  (* sign
     (cond
       [(= e 31) (if (zero? fraction) +inf.0 +nan.0)]
       [(zero? e) (exact->inexact (* fraction (expt 2 -24)))]
       [else (exact->inexact (* (+ 1024 fraction) (expt 2 (- e 25))))])))

(define (half->ordinal x)
  (define sign (if (negative? x) -1 1))
  (cond
    [(nan? x) #x7e00]
    [(infinite? x) (* sign #x7c00)]
    [(zero? x) 0]
    [else
     (define q (abs (inexact->exact x)))
     (* sign
        (if (< q (expt 2 -14))
            (round (* q (expt 2 24)))
            (let ([e (exponent q)])
              (+ (arithmetic-shift (+ e 15) 10) (- (round (* q (expt 2 (- 10 e)))) 1024)))))]))

(define <binary16>
  (make-representation #:name 'binary16
                       #:bf->repr (lambda (x)
                                    (if (bfzero? x)
                                        (bigfloat->flonum x)
                                        (half-round (bigfloat->real x))))
                       #:repr->bf (lambda (x)
                                    (parameterize ([bf-precision 24])
                                      (bf x)))
                       #:ordinal->repr ordinal->half
                       #:repr->ordinal half->ordinal
                       #:total-bits 16
                       #:special-value? nan?))

(define (exact-op operation . inputs)
  ;; Preserve IEEE behavior at zeros, infinities and NaNs. For ordinary inputs
  ;; use exact rational arithmetic and a single round-to-nearest-even step.
  (half-round (if (or (ormap (lambda (x) (or (nan? x) (infinite? x) (zero? x))) inputs))
                  (apply operation inputs)
                  (apply operation (map inexact->exact inputs)))))

(define-representation <binary16> #:cost 1)
(define-representation <binary32> #:cost 4)

(define-operation (neg.f16 [x <binary16>])
                  <binary16>
                  #:spec (neg x)
                  #:fpcore (! :precision binary16 (- x))
                  #:impl -
                  #:cost 1)
(define-operation (neg.f32 [x <binary32>])
                  <binary32>
                  #:spec (neg x)
                  #:fpcore (! :precision binary32 (- x))
                  #:impl -
                  #:cost 4)

(define-operations ([x <binary16>] [y <binary16>])
                   <binary16>
                   #:fpcore (! :precision binary16 _)
                   [+.f16 #:spec (+ x y) #:impl (lambda (x y) (exact-op + x y)) #:cost 1]
                   [-.f16 #:spec (- x y) #:impl (lambda (x y) (exact-op - x y)) #:cost 1]
                   [*.f16 #:spec (* x y) #:impl (lambda (x y) (exact-op * x y)) #:cost 1]
                   [/.f16 #:spec (/ x y) #:impl (lambda (x y) (exact-op / x y)) #:cost 4])

(define-operations ([x <binary32>] [y <binary32>])
                   <binary32>
                   #:fpcore (! :precision binary32 _)
                   [+.f32 #:spec (+ x y) #:impl (compose flsingle +) #:cost 4]
                   [-.f32 #:spec (- x y) #:impl (compose flsingle -) #:cost 4]
                   [*.f32 #:spec (* x y) #:impl (compose flsingle *) #:cost 4]
                   [/.f32 #:spec (/ x y) #:impl (compose flsingle /) #:cost 16])

(define-operation (f16->f32 [x <binary16>])
                  <binary32>
                  #:spec x
                  #:fpcore (! :precision binary32 (cast x))
                  #:impl identity
                  #:cost 1)
(define-operation (f32->f16 [x <binary32>])
                  <binary16>
                  #:spec x
                  #:fpcore (! :precision binary16 (cast x))
                  #:impl half-round
                  #:cost 1)
