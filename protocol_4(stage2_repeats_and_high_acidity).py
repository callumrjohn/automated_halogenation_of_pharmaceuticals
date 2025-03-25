from opentrons import protocol_api


# metadata
metadata = {
    'protocolName': 'protocol_4(stage2_repeats_and_high_acidity)',
    'author': 'Callum R. John <crj21@ic.ac.uk>',
    'description': 'HTE screening repeats and high TFA halogenation experiments (15, 25 TFA equivalents)',
    'apiLevel': '2.9'
}

def run(protocol: protocol_api.ProtocolContext):
    
    # LABWARE

    # Pipette tip racks
    tiprack1 = protocol.load_labware('opentrons_96_tiprack_300ul', 1)
    tiprack2 = protocol.load_labware('opentrons_96_tiprack_300ul', 4)
    tiprack3 = protocol.load_labware('opentrons_96_tiprack_300ul', 7)

    # Stock solution plates
    stock96 = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 5) # Substrates
    stock12 = protocol.load_labware('mettlertoledo_12_reservoir_24000ul', 2) # TFA soltutions, HFIP, and reagents
    
    # Reaction plates
    plate1 = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 3)
    plate2 = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 6)
    plate3 = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 9)
    plates = [plate1, plate2, plate3]

    # Pipette
    multi = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks = [tiprack1, tiprack2, tiprack3])
    protocol.max_speeds['Z'] = 200
    
    
    # STOCK SOLUTIONS

    substrates = stock96.rows()[0][0:3] # Substrate stock solution locations - A1, B1, C1: The first, second, and third columns of the stock96 plate
    hfip = stock12['A1'] # Neat HFIP
    tfa_dil = stock12['A2'] # TFA solution (2.00 M)
    tfa_conc = stock12['A3'] # TFA solution (8.33 M)
    pc = stock12['A4'] # Palau'chlor solution location
    nis = stock12['A5'] # NIS solution location
    nbs = stock12['A6'] # NBS solution location


    # TFA and HFIP dispense volumes
    # dictionaries tfa and hfip quantities for each well in a row (note that an "A1" well dispenses to all wells in a column i.e. A1, B1, C1, D1, E1, F1, G1, and H1)
    hfip_quantities = {'A1': 40, 'A2': 0, 'A3': 36, 'A4': 24, 'A5': 0, 'A6': 0, 'A7': 36, 'A8': 24, 'A9': 0, 'A10': 20, 'A11': 24, 'A12': 0} # Neat HFIP
    tfa_dil_quantities = {'A1': 20, 'A2': 60, 'A3': 0, 'A4': 0, 'A5': 0, 'A6': 60, 'A7': 0, 'A8': 0, 'A9': 0, 'A10': 40, 'A11': 0, 'A12': 0} # TFA solution (2.00 M)
    tfa_conc_quantities = {'A1': 0, 'A2': 0, 'A3': 24, 'A4': 36, 'A5': 60, 'A6': 0, 'A7': 24, 'A8': 36, 'A9': 60, 'A10': 0, 'A11': 36, 'A12': 60} # TFA solution (8.33 M)


    # DISPENSE FUNCTIONS    

    def premulti(solution): # Procedure to "prepare" each tip before use, ensuring accurate and consistent handling on solutions
        multi.pick_up_tip() # Pick up pipette tips
        
        # PRE-WETTING OF TIP
        for k in range (2):
            multi.aspirate(100, solution.bottom()) # Aspirate 100uL of solution form the source well
            multi.move_to(solution.top()) # Move to the top of the source well
            protocol.delay(seconds = 5) # Delay for 5 seconds
            multi.dispense(100, solution.top()) # Dispense 100uL of solution back into the source well
            multi.blow_out() # Blow out any remaining solution in/on the pipette tip
            
        # PRE-SATURATION OF TIP
        multi.move_to(solution.bottom()) # Move to the bottom of the source well
        multi.mix(2, 100) # Aspirate and dispense 100uL of solution 2 times


    def liq_hand(vol, asp_well, dis_well): # Proceedure to handle liquid transfers
        if count[0] == -1: # If the tips attached have not been used, prepare the tips
            premulti(asp_well)
            count[0] = 0
        if count[0] == 4: # If the tips attached have been used 4 times, drop tips in the trash and prepare new tips
            multi.drop_tip()        
            count[0] = 0
            premulti(asp_well)
                    
        multi.aspirate(vol, asp_well.bottom(), rate = 0.5) # Aspirate a specified volume of solution from a source well at half the default rate (default rate = 94 uL/s)
        protocol.delay(seconds = 1) # Delay for 1 second to allow solution remaining on the pipette tip to flow to the tip
        multi.touch_tip() # Touch the pipette tip to the inside wall of the stock well to remove residual solution
        multi.dispense(vol, dis_well.top(), rate = 0.5) # Dispense a specified volume of solution at the top of the destination well at half the default rate (default rate = 94 uL/s)
        multi.blow_out() # Blow out any remaining solution in/on the pipette tip

        count[0] = count[0] + 1 # Add 1 to the dispense count (used to determine when to drop tips and prepare new tips)


    # DISPENSE PROTOCOL

    count = [-1] # Initialise the dispense count to -1 (used to determine when to drop tips and prepare new tips)
    
    # Substrate dispenses
    for plate, substrate in zip(plates, substrates): # Iterate through each plate and substrate - 1 columns of substrates (8 solutions) per 96-well plate
        for wells in plate.rows()[0]:
            liq_hand(100, substrate, wells) # Dispense 100 uL of each substrate across a row within a plate

        if count[0] != 0: # Reset the tip count and drop tips if used tips are attached
            multi.drop_tip()
        count = [-1]


    #HFIP dispenses
    for plate in plates:
        for well, vol in hfip_quantities.items():
            if vol != 0: # In the API version used, it was noted that when "0" was specified as a dispense volume, the maximum pipette volume would be apeirated/dispensed instead, hence the need for this condition
                liq_hand(vol, hfip, plate[well]) # Dispense HFIP solution across the plate according to the hfip_quantities dictionary
        
    if count[0] != 0: # Reset the tip count and drop tips if used tips are attached
        multi.drop_tip()
    count = [-1]  
    
    # TFA solution (2.00 M) dispenses
    for plate in plates:
        for well, vol in tfa_dil_quantities.items():
            if vol != 0:
                liq_hand(vol, tfa_dil, plate[well]) # Dispense dilute TFA solution across the plate according to the tfa_dil_quantities dictionary

    if count[0] != 0:
        multi.drop_tip()
    count = [-1] # reset the tip count and drop tips if used tips are attached

    # TFA solution (8.33 M) dispenses
    for plate in plates:
        for well, vol in tfa_conc_quantities.items():
            if vol != 0:
                liq_hand(vol, tfa_conc, plate[well]) # Dispense conc TFA solution across the plate according to the tfa_conc_quantities dictionary
    
    if count[0] != 0:
        multi.drop_tip()
    count = [-1] # reset the tip count and drop tips if used tips are attached


    # Halogenating reagent dispenses

    # Palau'chlor dispenses
    for plate in plates:
        for well in plate.rows()[0][0:5]:
            liq_hand(40, pc, well) # Dispense 40 uL of NIS in columns 1-5 of each plate
    
    if count[0] != 0:
        multi.drop_tip()
    count = [-1] # reset the tip count and drop tips if used tips are attached

    # NIS dispenses
    for plate in plates:
        for well in plate.rows()[0][5:9]:
            liq_hand(40, nis, well) # Dispense 40 uL of NIS in columns 6-9 of each plate

    if count[0] != 0:
        multi.drop_tip()
    count = [-1] # reset the tip count and drop tips if used tips are attached

    # NBS dispenses
    for plate in plates:
        for well in plate.rows()[0][9:12]:
            liq_hand(40, nbs, well) # Dispense 40 uL of NBS in columns 10-12 of each plate

    if count[0] != 0:
        multi.drop_tip()
    count = [-1] # reset the tip count and drop tips if used tips are attached