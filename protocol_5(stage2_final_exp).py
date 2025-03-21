from opentrons import protocol_api


# metadata
metadata = {
    'protocolName': 'ptrocol_5(stage2_final_exp)',
    'author': 'Callum R. John <crj21@ic.ac.uk>',
    'description': 'Final halogenation screening',
    'apiLevel': '2.9'
}

def run(protocol: protocol_api.ProtocolContext):
    
    # LABWARE

    # Pipette tip racks
    tiprack1 = protocol.load_labware('opentrons_96_tiprack_300ul', 1)
    tiprack2 = protocol.load_labware('opentrons_96_tiprack_300ul', 4)

    # Stock solution plates
    stock96 = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 5) # Substrates
    stock12 = protocol.load_labware('mettlertoledo_12_reservoir_24000ul', 2) # TFA soltutions, HFIP, and reagents

    # Reaction plate
    plate = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 3)

    
    # Pipette
    multi = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks = [tiprack1, tiprack2])
    protocol.max_speeds['Z'] = 200

    
    
    # STOCK SOLUTIONS
    # Substrate stock solutions - A1 - H1: The first row of the stock96 plate
    # Halogenating reagnets - A2 - H2: The second row of the stock96 plate
    hfip_quantities = {'A1': 60, 'A2': 30, 'A4': 36, 'A5': 24, 'A7': 24, 'A9': 60, 'A10': 30, 'A11': 30} # Neat HFIP
    tfa_dil_quantities = {'A2': 30, 'A3': 60, 'A10': 30} # TFA solution (0.67 M)
    tfa_med_quantities = {'A4': 24, 'A5': 36, 'A6': 60, 'A11': 30} # TFA solution (3.33 M)
    tfa_conc_quantities = {'A7': 36, 'A8': 60} # TFA solution (8.33 M)


    # DISPENSE FUNCTIONS

    def premulti(solution): # Procedure to "prepare" each tip before use, ensuring accurate and consistent handling on solutions
        multi.pick_up_tip() # Pick up pipette tips

        # PRE-WETTING OF TIP
        for _ in range(2):
            multi.aspirate(100, solution) # Aspirate 100uL of solution from the source well
            multi.move_to(solution.top()) # Move to the top of the source well
            protocol.delay(seconds = 5) # Delay for 5 seconds
            multi.dispense(100, solution.top()) # Dispense 100uL of solution back into the source well
            multi.blow_out() # Blow out any remaining solution in/on the pipette tip
            
        # PRE-SAURATING OF TIP
        multi.move_to(solution.bottom(1)) # Move to the bottom of the source well
        multi.mix(2, 100) # Aspitate and dispense 100uL of solution 2 times


    def liq_hand(vol, asp_well, dis_well): # Proceedure to handle liquid transfers
        if count[0] == -1: # If the tips attached have not been used, prepare the tips
            premulti(asp_well)
            count[0] = 0
        if count[0] == 4: # If the tips attached have been used 4 times, drop tips in the trash and prepare new tips
            multi.drop_tip()        
            count[0] = 0
            premulti(asp_well)
                    
        multi.aspirate(vol, asp_well, rate = 0.5) # Aspirate a specified volume of solution from a source well at a specified height at half the default rate (default rate = 94 uL/s)
        multi.touch_tip() # Touch the pipette tip to the inside wall of the stock well to remove residual solution
        multi.dispense(vol, dis_well.top(), rate = 0.5) # Dispense a specified volume of solution at the top of the destination well at half the default rate (default rate = 94 uL/s)
        multi.blow_out() # Blow out any remaining solution in the pipette tip

        count[0] = count[0] + 1 # Add 1 to the dispense count (used to determine when to drop tips and prepare new tips)

    def count_check(): # Reset the tip count and drop tips if used tips are attached
        if count[0] != 0:
            multi.drop_tip()
        count = [-1]


    # DISPENSE PROTOCOL

    count = [-1] # Initialise the dispense count to -1 (used to determine when to drop tips and prepare new tips)
    
    # Substrate dispenses
    
    for wells in plate.rows()[0][:-1]:
        liq_hand(100, stock96['A1'], wells) # Dispense 100 uL of each substrate across the plate

    count_check() # Reset the tip count and drop tips if used tips are attached


    #HFIP dispenses
    for well, vol in hfip_quantities.items():
        liq_hand(vol, stock12['A1'], plate[well]) # Dispense HFIP solution across the plate according to the hfip_quantities dictionary
        
    count_check() # Reset the tip count and drop tips if used tips are attached
    

    # TFA dispenses
    for well, vol in tfa_dil_quantities.items():
        liq_hand(vol, stock12['A2'], plate[well]) # Dispense TFA (0.67 M) across the plate according to the tfa_dil_quantities dictionary

    count_check() # Reset the tip count and drop tips if used tips are attached
    
    for well, vol in tfa_med_quantities.items():
        liq_hand(vol, stock12['A3'], plate[well]) # Dispense TFA (3.33 M) across the plate according to the tfa_med_quantities dictionary

    count_check() # Reset the tip count and drop tips if used tips are attached

    for well, vol in tfa_conc_quantities.items():
        liq_hand(vol, stock12['A4'], plate[well]) # Dispense TFA (8.33 M) across the plate according to the tfa_conc_quantities dictionary

    count_check() # Reset the tip count and drop tips if used tips are attached


    #N-X dispenses
    for wells in plate.rows()[0][:-1]:
        liq_hand(40, stock96['A2'], wells) # Dispense 40 uL of each halogenating reagent across the plate

    count_check() # Reset the tip count and drop tips if used tips are attached