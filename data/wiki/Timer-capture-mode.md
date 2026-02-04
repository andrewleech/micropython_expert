Here the Timer can be used to measure an external signal and determine the timing period.

1. Select active input
  * in CCMRx reg - set CCxS bits to non-zero.
    * if zero the CCRx reg will be read-only.
2. Program filter and prescaler if required
  * filter: in CCMRx reg - write IC1F[3:0] bits
  * prescaler: write IC1PSC[1:0] bits
3. Program polarity
  * write CCxNP or CCxP bits to select between rising, falling, or both edges

You need two consecutive captures to determine timing of signal
Period is calculated by subtracting these two values where polarity_index = 1 if rising or falling edge is used and 2 id both.

```  Period = Capture(1) / (TIMx_CLK * (PSC+1) * (ICxPSC) * polarity_index(2))  ```

capture diff of CCRx_tn and CCRx_tn+1 is:
```
	if CCRx_tn < CCRx_tn+1:
		capture = CCRx_tn+1 - CCRx_tn
	else: capture = (ARR_max - CCRx_tn) + CCRx_tn+1
```
To facilitate input capture - we reset the timer counter after each rising edge by
* select TIxFPx as input trigger - in TMCR reg - set TS bits
* select reset mode as slave mode - in SMCCR reg - config SMS bits

So when an edge is detected, the counter is reset and period of ext signal is given by CCRx register. (ICPSC reg is not considered).

Period is given by:

```  Period = CCRx / (TIMx_CLK * (PSC+1)* polarity_index(1))```

###Timer output compare mode
Several output compare modes exist. You can use them to control an output waveform or to indicate when a period of time has elapsed.
* output compare timing
  * comparing CCRx and CNT has no effect on output.
  * used to generate a timing base
* output compare active
  * set channel output to active level on match
  * OCxRef signal is forced high when CNT matches CCRx (the capture/compare reg)
* output compare inactive
  * set channel to inactive level on match
  * OCxRef signal is forced low when CNT matches CCRx
* output compare toggle
  * OCxRef toggles when CNT matches CCRx
* output compare forced active/inactive
  * OCxRef is forced high(active mnode) or low (inactivemode) independently of CNT value


To configure Timer into one of these modes:

1. select clock source
2. in ARR and CCRx reg - write desired data
3. Configure output mode:
  * select output compare mode: timing/active/inactive/toggle
  * if not timing - in CCER reg - select polarity by writing CCxP
  * disable preload for CCx - in CCMRx reg - write OCxPE
  * enable capture/compare - in CCMRx - write CCxE
4. Enable counter:
  * in TIMx_CR1 reg - set CEN bit
5. If DMA/Interrupt is required - set CCxIE or CCxDE bit


Calculate update rate - compare timing / toggle of Timer output

```   CCx update rate = TIMx_Counter_CLK / CCRx```

where:
* if internal clock: ```TIMx_Counter_CLK = TIM_CLK / (PSC+1)```
* if external clock mode 1 or mode 2 ```  TIMx_Counter_CLK = ETR_CLK / ((ETR_PSC)*(PSC+1))```


Calculate delay - compare active/inactive Timer output
* ```  CCx delay = CCRx / TIMx_Counter_CLK```
where:
* if internal clock: ```TIMx_Counter_CLK = TIM_CLK / (PSC+1)```
* if external clock mode 1 or mode 2 ```  TIMx_Counter_CLK = ETR_CLK / ((ETR_PSC)*(PSC+1))```
* if internal trigger clock: ```  TIMx_Counter_CLK = ITRx_CLK / (PSC+1)```
