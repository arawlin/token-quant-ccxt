# dynamic balance

## question

1. 价值变动率 r' 与 价格变动 p' 的关系？

   ![formule](./resources/formule.jpg)

   $\frac{q \cdot p_n}{q\cdot p_n + a} = 0.5 + \Delta r$

   $p_n = p_o \cdot (1 + \Delta p)$

   $\Delta p = 1 - \frac{a \cdot (0.5 + r)}{q \cdot (0.5 - r) \cdot p_o}$

2. 当价格下跌买入的，是否会在价格上涨但是价格没有回到原来位置时，将买入的以这个价格卖出，这样的话，将会导致亏损，会这样吗？

## formula

$\Delta a = |\frac{a_0 - q_0\cdot p_1}{2}|$

$\Delta q = |\frac{a_0 / p_1 - q_0}{2}|$

当价格下跌，然后再次涨起时

$a_p = a_0 - \Delta a_1 + \Delta a_2 - a_0 >= \Delta a_1 \cdot fee + \Delta a_2 \cdot fee$

$(1 - fee) \cdot \Delta a_2 - (1 + fee) \cdot \Delta a_1 >= 0$

$\Delta a_1 = |\frac{a_0 - q_0\cdot p_1}{2}|$

$\Delta a_2 = |\frac{a_1 - q_1\cdot p_2}{2}|$

$a_1 = a_0 + \Delta a_1$

$q_1 = q_0 + \Delta q_1$

## example

```cmd
1000        1                                         1000

950         1+25/950=1.026                              975                         25 * 0.001 = 0.025

975         1.026 - 12.675/975=1.013                    975 + 12.675 = 987.675
(1.026*975 - 975)/2=12.675/976=0.013

1000        1.013 - 0.012662 = 1.000338                 987.675 + 12.662 = 1000.337
(1.013 * 1000 - 987.675)/ 2 =  12.662 / 1000 = 0.012662
```
