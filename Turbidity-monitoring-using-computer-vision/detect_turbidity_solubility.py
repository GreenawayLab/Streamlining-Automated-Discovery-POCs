from turbidity_solubility import mxTurbidityMonitor
import time

#need to change the path on the pi
mtm = mxTurbidityMonitor('C:/path-to-folder/Turbidity-monitoring-using-computer-vision/',
                         tm_n_minutes=1,
                         tm_range_limit=3,
                         tm_std_max=2, #std_max: maximum standard deviation the data can have to be determined as stable
                         tm_sem_max=2, #sem_max: maximum standard error the data can have to be determined as stable
                         tm_upper_limit=1
                         )
try:
    start_time = time.time()
    #mtm.start_monitoring(roi_path='C:/path-to-folder/Turbidity-monitoring-using-computer-vision-main/solubility_study_X/vision_selections.json') # add this in after selecting the first ROI and saving it, to use as the ROI for the rest of the experiments
    mtm.start_monitoring()
    
    time.sleep(10)
    while True:
        time.sleep(10)
        x, y = mtm.get_turbidity_data()
        print(mtm.state, x[-1], y[-1])

        if mtm.state != 'unstable_state':
            print(f'Finished: {mtm.state}')
            mtm.stop_monitoring()
            break
        elif time.time() - start_time >= 200:
            print('3 min reached')
            print(mtm.state)
            mtm.stop_monitoring()
            break


except KeyboardInterrupt as e:
    print('Keyboard Interrupt')
    mtm.stop_monitoring()
    exit(1)
    
