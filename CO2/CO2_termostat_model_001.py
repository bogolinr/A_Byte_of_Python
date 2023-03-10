from decimal import Decimal
import math
import numpy as np
import matplotlib.pyplot as plt

TempCabinet = 25				#начальная температура.
'''начальная температура.'''
TempUstavka = 30				#целевая температура, которую должен поддерживать термостат.
'''целевая температура, которую должен поддерживать термостат.'''
Temp = TempCabinet				#текущая температура термостата.
'''текущая температура термостата.'''
TempDiff = 0
'''ошибка управления по температуре'''
Temp_before_Inerc = 0
'''температура в момент начала инерционного нагрева.'''
Temp_before_Cooling = TempCabinet	#температура в момент начала охлаждения. Нужна для расчёта текущей температуры при охлжадении.
'''температура в момент начала охлаждения.'''
Cooling = 0
'''остывание'''
TimeMod = 400					#длительность моделирования.
'''длительность моделирования.'''
TimeStep = 0.1					#шаг изменеиня времени, значение должно быть кратно целым числам.
'''шаг изменеиня времени, значение должно быть кратно целым числам.'''
Time_Inerc_duration = 0					# момент окончания инерционнго нагрева, рассчитывается как функция длительности непрерывного ключения нагревателя и текущего времени.
'''момент окончания инерционного нагрева.'''
Time_Inerc = 0					#время от начала инерционного нагрева.
'''время от начала инерционного нагрева.'''
Time_Сooling = 0					#время от начала остывания.
'''время от начала остывания.'''
t = 0							#переменная времени.
'''переменная времени.'''
PWM_period = 4					#период шим генератора в секундах.
'''период шим генератора в секундах.'''
PWM_ON = 0							#текущее значение ШИМ генератора, меняется от 0 до PWM_period секунд.
'''длинна импульса ШИМ генератора в текущем периоде, меняется от 0 до PWM_period секунд.'''
PWM_min = 1						#минимальная длинна импульса ШИМ в секундах.
'''минимальная длинна импульса ШИМ в секундах.'''
PWM_Step = PWM_period/PWM_min
'''сколько раз PWM_min укладывается в PWM_period.'''
PWM_N = 0
'''число прошедших периодов ШИМ.'''
Ten = False						#флаг включения нагревателя.
'''флаг включения нагревателя.'''
Ten_time_on = 0				#длительность непрерывного включения нагревателя. Нужен для расчёта длительности инерционного нагрева.
'''длительность непрерывного включения нагревателя.'''
Inertia = False						#флаг инерционного нагрева.
'''флаг инерционного нагрева.'''
Number_of_decimals = 2
'''количество знаков после запятой'''
K_proportionally = 10			#коэффициэкнт пропорциональной составляющей.
'''коэффициэкнт пропорциональной составляющей.'''
Integral = 60					#время интегрирования ПИД регулятора в секундах.
'''время интегрирования ПИД регулятора в секундах'''
arr_Temp_Integral = [(TempUstavka - TempCabinet)] * Integral	#массив предыдущих температур за время интегрирования.
'''массив предыдущих температур за время интегрирования'''
K_integral = 1e-2					#коэффициэнт интегральной составляющей.
'''коэффициэнт интегральной составляющей.'''
Differential = 1					#смещение по массиву температур: difTemp=Temp(i)-Temp(i-3)
'''смещение по массиву температур: difTemp=Temp(i)-Temp(i-3)'''
K_differential = 0.1				#коэффициэнт дифференциальной составляющей.
'''коэффициэнт дифференциальной составляющей.'''
while t <= TimeMod:
	TempDiff = TempUstavka - Temp
	
	#Реальный датчик температуры выдаёт значения один раз в секунду, поэтому записываем в массив
	#данные температуры,полученные в целые значения текущего времени.
	if int(t) == t:
		arr_Temp_Integral.append(round(TempDiff,Number_of_decimals))    #добавляет ошибку температуры в конец массива.
		del arr_Temp_Integral[0]
		#Вычисляем реакцию ПИД регулятора на сигнал ошибки
		PID_proportionally = K_proportionally * TempDiff
		PID_integral = K_integral * sum(arr_Temp_Integral)
		PID_differential = K_differential*(TempDiff - arr_Temp_Integral[-1 * Differential])
		PID = PID_proportionally + PID_integral + PID_differential
	#ШИМ генератор
	if (PWM_N==int(t / PWM_period)):
		PWM_N = PWM_N+1
		if (PID>=1):
			PWM_ON = PWM_period
		if (PID>=0) and (PID<=1):
			PWM_ON = PWM_min * round(PID*PWM_Step)
		if (PID<=0):
			PWM_ON = 0
	if (t-(PWM_N-1) * PWM_period < PWM_ON):	# проверяем включен ли ШИМ в данный момент времени.
		Ten = True
		Time_Сooling = 0
		Temp = Temp + 160 * (1-2.115384 * math.exp(-1 / 1100 * Ten_time_on) + 1.115384 * math.exp(-1 / 580 * Ten_time_on))
		Ten_time_on = Ten_time_on + TimeStep
	else:
		#Расчитываем время инерционного нагрева один раз после выключения тена.
		if (Ten == True):
			Ten = False
			Time_Inerc_duration = t + 650 * (1-math.exp(-1 / 20 * Ten_time_on))
			Ten_time_on = 0
			Inertia = True
			Temp_before_Inerc = Temp
		#Изменение температуры при инерционном нагреве.
		if(t<=Time_Inerc_duration) and (Ten == False):
			Time_Inerc = Time_Inerc + TimeStep
			Temp = Temp_before_Inerc + 5.75 * (1 - 1 / math.exp(Time_Inerc/ 146))
		else:
			#Остывание
			#В первый момент остывания
			if (Inertia == True):
				Time_Inerc_duration = 0
				Time_Inerc = 0
				Inertia = False
				Temp_before_Cooling = Temp
			#Изменение температуры при остывании.
			Time_Сooling = Time_Сooling + TimeStep
			Cooling = (Temp_before_Cooling - TempCabinet) * math.exp(-1 /4173 * Time_Сooling)
			Temp = TempCabinet + Cooling
			# Temp = TempCabinet + (Temp_before_Cooling - TempCabinet) * math.exp(-1 /4173 * Time_Сooling)
 			
	print('t=', round(t,1), 'PID=', round(PID,1), 'Temp=',round(Temp,2), 'Ten=', Ten, 'Cooling=',round(Cooling,3), 'Time_Сooling=',round(Time_Сooling,1), 'Time_Inerc=',round(Time_Inerc,1))
	#print('PID=',PID)
	#print('Temp=',Temp)
    #Вычисляем следующее значение времени
	t = round((t + TimeStep),Number_of_decimals)
	
	
	
	
	#print(arr_Temp_Integral)
	
	# Temp = Temp + TimeStep
	



