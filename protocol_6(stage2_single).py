from opentrons import protocol_api


# metadata
metadata = {
    'protocolName': 'protocol_6(stage2_single)',
    'author': 'Callum R. John <crj21@ic.ac.uk>',
    'description': 'Protocol for screening a single halogenation',
    'apiLevel': '2.9'
}

def run(protocol: protocol_api.ProtocolContext):
    
    # LABWARE

    # Pipette tip racks
    tiprack1 = protocol.load_labware('opentrons_96_tiprack_300ul', 1)
    tiprack2 = protocol.load_labware('opentrons_96_tiprack_300ul', 4)

    # Stock solution plates
    stock96 = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 5) # TFA solutions and HFIP
    stock12 = protocol.load_labware('mettlertoledo_12_reservoir_24000ul', 2) # Substrate and reagent

    # Reaction plate
    plate = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 3)

    # Pipette
    multi = protocol.load_instrument('p300_multi_gen2', 'right', tip_racks = [tiprack1])
    single = protocol.load_instrument('p300_single_gen2', 'left', tip_racks = [tiprack2])
    protocol.max_speeds['Z'] = 200

    # STOCK SOLUTIONS
    # Substrate stock solutions - A1 - H1: The first row of the stock96 plate
    # Halogenating reagnets - A2 - H2: The second row of the stock96 plate
    hfip_quantities = {'A1': 60, 'B1': 30, 'D1': 36, 'E1': 24, 'G1': 24} # Neat HFIP
    tfa_dil_quantities = {'B1': 30, 'C1': 60} # TFA solution (0.67 M)
    tfa_med_quantities = {'D1': 24, 'E1': 36, 'F1': 60} # TFA solution (3.33 M)
    tfa_conc_quantities = {'G1': 36, 'H1': 60} # TFA solution (8.33 M)

    count = [-1] # Initialise the dispense count to -1 (used to determine when to drop tips and prepare new tips)

    # DISPENSE FUNCTIONS

    def preppipette(pipette, solution): # Procedure to "prepare" each tip before use, ensuring accurate and consistent handling on solutions
        pipette.pick_up_tip() # Pick up pipette tips

        # PRE-WETTING OF TIP
        for _ in range(2):
            pipette.aspirate(100, solution) # Aspirate 100uL of solution from the source well
            pipette.move_to(solution.top()) # Move to the top of the source well
            protocol.delay(seconds = 5) # Delay for 5 seconds
            pipette.dispense(100, solution.top()) # Dispense 100uL of solution back into the source well
            pipette.blow_out() # Blow out any remaining solution in/on the pipette tip
            
        # PRE-SAURATING OF TIP
        pipette.move_to(solution.bottom(1)) # Move to the bottom of the source well
        pipette.mix(2, 100) # Aspitate and dispense 100uL of solution 2 times


    def liq_hand(pipette, vol, asp_well, dis_well): # Proceedure to handle liquid transfers
        if count[0] == -1: # If the tips attached have not been used, prepare the tips
            preppipette(pipette, asp_well)
            count[0] = 0
        if count[0] == 4: # If the tips attached have been used 4 times, drop tips in the trash and prepare new tips
            pipette.drop_tip()        
            count[0] = 0
            preppipette(pipette, asp_well)
                    
        pipette.aspirate(vol, asp_well, rate = 0.5) # Aspirate a specified volume of solution from a source well at a specified height at half the default rate (default rate = 94 uL/s)
        pipette.touch_tip() # Touch the pipette tip to the inside wall of the stock well to remove residual solution
        pipette.dispense(vol, dis_well.top(), rate = 0.5) # Dispense a specified volume of solution at the top of the destination well at half the default rate (default rate = 94 uL/s)
        pipette.blow_out() # Blow out any remaining solution in the pipette tip

        count[0] = count[0] + 1 # Add 1 to the dispense count (used to determine when to drop tips and prepare new tips)

    def count_check(pipette): # Reset the tip count and drop tips if used tips are attached
        if count[0] != 0:
            pipette.drop_tip()
        count[:] = [-1]


    # DISPENSE PROTOCOL
    
    # Substrate dispenses
    liq_hand(multi, 100, stock12['A1'], plate['A1'])

    count_check(multi) # Reset the tip count and drop tips if used tips are attached

    #HFIP dispenses
    for well, vol in hfip_quantities.items():
        liq_hand(single, vol, stock96['A1'], plate[well]) # Dispense HFIP solution across the plate according to the hfip_quantities dictionary
        
    count_check(single) # Reset the tip count and drop tips if used tips are attached

    # TFA dispenses
    for well, vol in tfa_dil_quantities.items():
        liq_hand(single, vol, stock96['B1'], plate[well]) # Dispense TFA (0.67 M) across the plate according to the tfa_dil_quantities dictionary

    count_check(single) # Reset the tip count and drop tips if used tips are attached
    
    for well, vol in tfa_med_quantities.items():
        liq_hand(single, vol, stock96['C1'], plate[well]) # Dispense TFA (3.33 M) across the plate according to the tfa_med_quantities dictionary

    count_check(single) # Reset the tip count and drop tips if used tips are attached

    for well, vol in tfa_conc_quantities.items():
        liq_hand(single, vol, stock96['D1'], plate[well]) # Dispense TFA (8.33 M) across the plate according to the tfa_conc_quantities dictionary

    count_check(single) # Reset the tip count and drop tips if used tips are attached

    # Halogenating reagent dispense
    liq_hand(multi, 100, stock12['A2'], plate['A1'])

    count_check(multi) # Reset the tip count and drop tips if used tips are attached