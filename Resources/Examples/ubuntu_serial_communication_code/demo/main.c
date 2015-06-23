/***********************************************
 *Documentation for E-Yantra
 *Author List:			Aniket Patel, Mukesh P
 *Filename:			main.c
 *Theme: 			Cargo Sorting
 *Functions: 			lcd_port_config (void)
				buzzer_pin_config (void)
				motion_pin_config (void)
				timer5_init()
				velocity (unsigned char left_motor, unsigned char right_motor)
				motion_set (unsigned char Direction)
				forward (void)
				stop (void)
				right (void)
				left()
				port_init()
				buzzer_on (void)
				buzzer_off (void)
				uart2_init(void)
				SIGNAL(USART2_RX_vect)
				init_devices()
 *Global Variables:		data, x, y
 *Note: The code hereby is the Universal Code for the Cargo-Sorting theme. 
 *(It will work for any configuration of the prescribed theme within predetermined limits)

**************************************************/
#include<avr/io.h>
#include<avr/interrupt.h>
#include<util/delay.h>
#include "lcd.c"

unsigned char data; //to store received data from UDR1
int x = 255,y = 255;

/*
 * Function Name:	lcd_port_config
 * Input:		none
 * Output: 		Configures the lcd port
 * Logic:		Enables the DDRC register and setting pins of PORTC
 * Example Call:	lcd_port_config ();
 *
 */	
void lcd_port_config (void)
{
	DDRC = DDRC | 0xF7; //setting all the LCD pin's direction set as output
	PORTC = PORTC & 0x80; //setting all the LCD pins are set to logic 0 except PORTC 7
}

/*
 * Function Name:	buzzer_pin_config
 * Input:		none
 * Output: 		Configures the buzzer pin
 * Logic:		Enables the DDRC register and setting pin of PORTC 7
 * Example Call:	buzzer_pin_config ()
 *
 */	
void buzzer_pin_config (void)
{
 DDRC = DDRC | 0x08;		//Setting PORTC 3 as outpt
 PORTC = PORTC & 0xF7;		//Setting PORTC 3 logic low to turnoff buzzer
}

/*
 * Function Name:	motion_pin_config
 * Input:		none
 * Output: 		Configures the pins for motion
 * Logic:		Enables the DDRA register and setting pins of PORTA and enables the DDRL Register
 * Example Call:	motion_pin_config ()
 */	
void motion_pin_config (void)
{
 DDRA = DDRA | 0x0F;
 PORTA = PORTA & 0xF0;
 DDRL = DDRL | 0x18;   //Setting PL3 and PL4 pins as output for PWM generation
 PORTL = PORTL | 0x18; //PL3 and PL4 pins are for velocity control using PWM.
}

/*
 * Function Name:	timer5_init()
 * Input:		none
 * Output: 		Configures the pins for timer use
 * Logic:		Commented below
 * Example Call:	timer5_init()
 */
void timer5_init()
{
	TCCR5B = 0x00;	//Stop
	TCNT5H = 0xFF;	//Counter higher 8-bit value to which OCR5xH value is compared with
	TCNT5L = 0x01;	//Counter lower 8-bit value to which OCR5xH value is compared with
	OCR5AH = 0x00;	//Output compare register high value for Left Motor
	OCR5AL = 0xFF;	//Output compare register low value for Left Motor
	OCR5BH = 0x00;	//Output compare register high value for Right Motor
	OCR5BL = 0xFF;	//Output compare register low value for Right Motor
	OCR5CH = 0x00;	//Output compare register high value for Motor C1
	OCR5CL = 0xFF;	//Output compare register low value for Motor C1
	TCCR5A = 0xA9;	/*{COM5A1=1, COM5A0=0; COM5B1=1, COM5B0=0; COM5C1=1 COM5C0=0}
 					  For Overriding normal port functionality to OCRnA outputs.
				  	  {WGM51=0, WGM50=1} Along With WGM52 in TCCR5B for Selecting FAST PWM 8-bit Mode*/

	TCCR5B = 0x0B;	//WGM12=1; CS12=0, CS11=1, CS10=1 (Prescaler=64)
}

/*
 * Function Name:	velocity()
 * Input:		speed of left_motor, right_motor
 * Output: 		the value is stored in the OCR pins. This value sets the voltage across the motors. 255 indicates 12 V and 0 indicates 				0 V
 * Logic:		Assignment of char value to the pin
 * Example Call:	velocity(200,200)
 */
void velocity (unsigned char left_motor, unsigned char right_motor)
{
	OCR5AL = (unsigned char)left_motor;
	OCR5BL = (unsigned char)right_motor;
}

/*
 * Function Name:	motion_set()
 * Input:		sets the required pins for movement
 * Output: 		enables the necessary PORTA pins
 * Logic:		the required pins of the PORTA pins are set so that the robot can move left or right.
 * Example Call:	motion_set(0x01)
 */
void motion_set (unsigned char Direction)
{
 unsigned char PortARestore = 0;

 Direction &= 0x0F; 			// removing upper nibbel as it is not needed
 PortARestore = PORTA; 			// reading the PORTA's original status
 PortARestore &= 0xF0; 			// setting lower direction nibbel to 0
 PortARestore |= Direction; 	// adding lower nibbel for direction command and restoring the PORTA status
 PORTA = PortARestore; 			// setting the command to the port
}

/*
 * Function Name:	forward()
 * Input:		None
 * Output: 		sets pins for forward movement
 * Logic:		sets pins of PORTA for forward movement
 * Example Call:	forward()
 */
void forward (void) //both wheels forward
{
  motion_set(0x06);
}

/*
 * Function Name:	stop()
 * Input:		None
 * Output: 		sets pins for stopping
 * Logic:		sets pins of PORTA for to stop the robot
 * Example Call:	stop()
 */
void stop (void)
{
  motion_set(0x00);
}

/*
 * Function Name:	left()
 * Input:		None
 * Output: 		sets pins for left turn
 * Logic:		sets pins of PORTA for to turn the robot left and sets the velocity of the wheel
 * Example Call:	left()
 */
void left (void) //Left wheel backward, right wheel stationary
{
 motion_set(0x01);
 velocity(200,0);
}

/*
 * Function Name:	right()
 * Input:		None
 * Output: 		sets pins for right turn
 * Logic:		sets pins of PORTA for to turn the robot right and sets the velocity of the wheel
 * Example Call:	right()
 */
void right (void) //Left wheel stationary, Right wheel backward
{
 motion_set(0x08);
 velocity(0,200);
}

//Function to initialize ports
/*
 * Function Name:	port_init()
 * Input:		None
 * Output: 		initializes the required ports of Fire bird V
 * Logic:		calls the pin config functions
 * Example Call:	port_init()
 */
void port_init()
{
	motion_pin_config();
	buzzer_pin_config();
	lcd_port_config();//lcd pin configuration
}

/*
 * Function Name:	buzzer_on()
 * Input:		None
 * Output: 		Buzzer beeps
 * Logic:		sets the PORTC pin on for buzzer beep
 * Example Call:	buzzer_on()
 */
void buzzer_on (void)
{
 unsigned char port_restore = 0;
 port_restore = PINC;
 port_restore = port_restore | 0x08;
 PORTC = port_restore;
}

/*
 * Function Name:	buzzer_off()
 * Input:		None
 * Output: 		Buzzer stops beeping
 * Logic:		sets the PORTC pin off for stopping buzzer beep
 * Example Call:	buzzer_off()
 */
void buzzer_off (void)
{
 unsigned char port_restore = 0;
 port_restore = PINC;
 port_restore = port_restore & 0xF7;
 PORTC = port_restore;
}

//Function To Initialize UART2
// desired baud rate:9600
// actual baud rate:9600 (error 0.0%)
// char size: 8 bit
// parity: Disabled
/*
 * Function Name:	uart2_init()
 * Input:		None
 * Output: 		UART2 initialization
 * Logic:		No logic
 * Example Call:	uart2_init()
 */
void uart2_init(void)
{
 UCSR2B = 0x00; //disable while setting baud rate
 UCSR2A = 0x00;
 UCSR2C = 0x06;
 UBRR2L = 0x5F; //set baud rate lo
 UBRR2H = 0x00; //set baud rate hi
 UCSR2B = 0x98;
}

/*
 * Function Name:	SIGNAL()
 * Input:		Interrupt USART2_RX_vect
 * Output: 		sets the velocity of the wheels
 * Logic:		It stores data from UDR2 in a variable and using switch cases it sets the desired velocity
 * Example Call:	No call as it is an interrupt
 */
SIGNAL(USART2_RX_vect) 		// ISR for receive complete interrupt
{
	data = UDR2; 				//making copy of data from UDR2 in 'data' variable

	//UDR2 = data;
	switch(data)
	{
        case 0x00: x = 255; y = 255; break;
        case 0x01: x = 200; y = 255; break;
        case 0x02: x = 150; y = 255; break;
        case 0x03: x = 100; y = 255; break;
        case 0x04: x = 50;  y = 255; break;
        case 0x10: x = 255; y = 200; break;
        case 0x11: x = 200; y = 200; break;
        case 0x12: x = 150; y = 200; break;
        case 0x13: x = 100; y = 200; break;
        case 0x14: x = 50;  y = 200; break;
        case 0x20: x = 255; y = 150; break;
        case 0x21: x = 200; y = 150; break;
        case 0x22: x = 150; y = 150; break;
        case 0x23: x = 100; y = 150; break;
        case 0x24: x = 50;  y = 150; break;
        case 0x30: x = 255; y = 100; break;
        case 0x31: x = 200; y = 100; break;
        case 0x32: x = 150; y = 100; break;
        case 0x33: x = 255; y = 255; break;
        case 0x34: x = 50;  y = 150; break;
        case 0x40: x = 255; y = 50;  break;
        case 0x41: x = 200; y = 50;  break;
        case 0x42: x = 150; y = 50;  break;
        case 0x43: x = 150; y = 50;  break;
        case 0x44: right();          return;
        case 0x45: left();           return;
        case 0x35: x = 0;   y = 0;   break;
	}
        forward();
        velocity(x,y);
        lcd_print(1,1,x,5);
        lcd_print(2,1,y,5);
}


//Function To Initialize all The Devices
/*
 * Function Name:	init_devices()
 * Input:		none
 * Output: 		initializes all the devices
 * Logic:		None
 * Example Call:	init_devices()
 */
void init_devices()
{
 cli(); //Clears the global interrupts
 port_init();  //Initializes all the ports
 uart2_init(); //Initailize UART1 for serial communiaction
 timer5_init();
 sei();   //Enables the global interrupts
}

//Main Function
int main(void)
{
	init_devices();
	lcd_reset_4bit();
    	lcd_init();
	while(1);
}