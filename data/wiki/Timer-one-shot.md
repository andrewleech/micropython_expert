This is a specific setting of input and output capture mode. The counter starts in response to a stimulus and then generates a pulse of specific length after a specific delay.
```
   Delay = CCRy / (TIMx_CLK / (PSC + 1))
   Pulse length = (ARR - CCRy) / (TIMx_CLK / (PSC + 1))
```
###To configure:
1. confgure input pin and mode
  * select TIxFPx trigger to be used
    * in CCMRx reg - write CCxS bits
  * select polarity of input (pos, neg, both)
    * in CCER reg - write CCxP and CCxNP bits
  * configure TIxFPx trigger to slave mode
    * in SMCR reg - write TS bits	
  * select trigger mode to slave mode
    * in SMCR reg - write SMS bits
2. configure output pin and mode
  * select output polarity
		- in CCER reg - write CCyP bit
  * select output compare mode
    * in CCMRy reg - write OCyM bits
    * PWM1 or PWM2 mode
  * set delay value
    * in CCRy reg - write delay value
  * set autoreload to have desired pulse
  * ```pulse = TIMy_ARR - TIMy_CCRy```
3. select one-pulse mode if only need one pulse (else reset bit)
  * in CR1 reg - set OPM bit
