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
    tiprack4 = protocol.load_labware('opentrons_96_tiprack_300ul', 10)

    # Stock solution plates
    stock96 = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 5) # Substrates
    stock12 = protocol.load_labware('mettlertoledo_12_reservoir_24000ul', 2) # TFA soltutions, HFIP, and reagents
    
    # Reaction plates
    plate1 = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 3)
    plate2 = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 6)
    plate3 = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 9)
    plates = [plate1, plate2, plate3]

    # Pipette
    multi = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks = [tiprack1, tiprack2, tiprack3, tiprack4])
    protocol.max_speeds['Z'] = 200
    
    
    
    # STOCK SOLUTIONS

    substrates = stock96.rows()[0][0:3] # Substrate stock solution locations - A1, B1, C1: The first, second, and third columns of the stock96 plate
    substrate_vol = 800 #uL
    sub_height_t0 = substrate_vol/(stock96['A1'].length*stock96['A1'].width) # Calculate the height of the substrate solution in eeach substrate well before the first dispense
    sub_depth_t0 = sub_height_t0 - 3 # Add a grace height of 3mm to the calculated height to ensure the pipette tip is submerged in the solution

    hfip = stock12['A1'] # Neat HFIP
    tfa_dil = stock12['A2'] # Dilute TFA solution
    tfa_conc = stock12['A3'] # Concentrated TFA solution
    pc = stock12['A4'] # Palau'chlor solution location
    nis = stock12['A5'] # NIS solution location
    nbs = stock12['A6'] # NBS solution location

    sub_total = 12 # Total number of dispenses for each substrate i.e 12 reactions being prepared with 12 dispenses of substrate

    # TFA and HFIP dispense volumes
    # dictionaries tfa and hfip quantities for each well in a row (note that an "A1" well dispenses to all wells in a column i.e. A1, B1, C1, D1, E1, F1, G1, and H1)
    hfip_quantities = {'A1': 40, 'A2': 0, 'A3': 36, 'A4': 24, 'A5': 0, 'A6': 0, 'A7': 36, 'A8': 24, 'A9': 0, 'A10': 20, 'A11': 24, 'A12': 0} # Neat HFIP
    tfa_dil_quantities = {'A1': 20, 'A2': 60, 'A3': 0, 'A4': 0, 'A5': 0, 'A6': 60, 'A7': 0, 'A8': 0, 'A9': 0, 'A10': 40, 'A11': 0, 'A12': 0} # TFA solution (2.00 M)
    tfa_conc_quantities = {'A1': 0, 'A2': 0, 'A3': 24, 'A4': 36, 'A5': 60, 'A6': 0, 'A7': 24, 'A8': 36, 'A9': 60, 'A10': 0, 'A11': 36, 'A12': 60} # TFA solution (8.33 M)


    # DISPENSE FUNCTIONS    

    def premulti(solution, height_t0, well_count, total): # Procedure to "prepare" each tip before use, ensuring accurate and consistent handling on solutions
        multi.pick_up_tip() # Pick up pipette tips
        
        # PRE-WETTING OF TIP
        for k in range (2):
            multi.aspirate(100, solution.bottom(height_t0 - height_t0*well_count[0]/total)) # Aspirate 100uL of solution from the source well from a specified height
            multi.move_to(solution.top()) # Move to the top of the source well
            protocol.delay(seconds = 5) # Delay for 5 seconds
            multi.dispense(100, solution.top()) # Dispense 100uL of solution back into the source well
            multi.blow_out() # Blow out any remaining solution in/on the pipette tip
            
        # PRE-SATURATION OF TIP
        multi.move_to(solution.bottom(height_t0 - height_t0*well_count[0]/total)) # Move to a specified height within the source well
        multi.mix(2, 100) # Aspirate and dispense 100uL of solution 2 times


    def liq_hand(vol, asp_well, dis_well, height_t0, well_count, total): # Proceedure to handle liquid transfers
        if count[0] == -1: # If the tips attached have not been used, prepare the tips
            premulti(asp_well, height_t0, well_count, total)
            count[0] = 0
        if count[0] == 4: # If the tips attached have been used 4 times, drop tips in the trash and prepare new tips
            multi.drop_tip()        
            count[0] = 0
            premulti(asp_well, height_t0, well_count, total)
                    
        well_count[0] = well_count[0] + 1 # Add 1 to the well count each dispense (used to calculate the height of the solution in the source well)
        multi.aspirate(vol, asp_well.bottom(height_t0 - height_t0*well_count[0]/total), rate = 0.5) # Aspirate a specified volume of solution from a source well at a specified height at half the default rate (default rate = 94 uL/s)
        multi.dispense(vol, dis_well.top(), rate = 0.5) # Dispense a specified volume of solution at the top of the destination well at half the default rate (default rate = 94 uL/s)
        multi.blow_out() # Blow out any remaining solution in/on the pipette tip

        count[0] = count[0] + 1 # Add 1 to the dispense count (used to determine when to drop tips and prepare new tips)


    # DISPENSE PROTOCOL

    count = [-1] # Initialise the dispense count to -1 (used to determine when to drop tips and prepare new tips)
    
    # Substrate dispenses
    for plate, substrate in zip(plates, substrates): # Iterate through each plate and substrate - 1 columns of substrates (8 solutions) per 96-well plate
        substrate_count = [0]
        for wells in plate.rows()[0]:
            liq_hand(100, substrate, wells, sub_depth_t0, substrate_count, sub_total) # Dispense 100 uL of each substrate across a row within a plate

        if count[0] != 0: # Reset the tip count and drop tips if used tips are attached
            multi.drop_tip()
        count = [-1]


    #HFIP dispenses
    for plate in plates:
        for well, vol in hfip_quantities.items():
            if vol != 0:
                liq_hand(vol, hfip, plate[well], 0, [0], 1) # Dispense HFIP solution across the plate according to the hfip_quantities dictionary
        
    if count[0] != 0: # Reset the tip count and drop tips if used tips are attached
        multi.drop_tip()
    count = [-1]  
    
    # TFA solution (2.00 M) dispenses
    for plate in plates:
        for well, vol in tfa_dil_quantities.items():
            if vol != 0:
                liq_hand(vol, tfa_dil, plate[well], 0, [0], 1) # Dispense dilute TFA solution across the plate according to the tfa_dil_quantities dictionary

    if count[0] != 0:
        multi.drop_tip()
    count = [-1] # reset the tip count and drop tips if used tips are attached

    # TFA solution (8.33 M) dispenses
    for plate in plates:
        for well, vol in tfa_conc_quantities.items():
            if vol != 0:
                liq_hand(vol, tfa_conc, plate[well], 0, [0], 1) # Dispense conc TFA solution across the plate according to the tfa_conc_quantities dictionary
    
    if count[0] != 0:
        multi.drop_tip()
    count = [-1] # reset the tip count and drop tips if used tips are attached


    # Halogenating reagent dispenses

    # Palau'chlor dispenses
    for plate in plates:
        for well in plate.rows()[0][0:5]:
            liq_hand(40, pc, well, 0, [0], 1) # Dispense 40 uL of NIS in columns 1-5 of each plate
    
    if count[0] != 0:
        multi.drop_tip()
    count = [-1] # reset the tip count and drop tips if used tips are attached

    # NIS dispenses
    for plate in plates:
        for well in plate.rows()[5:9]:
            liq_hand(40, nis, well, 0, [0], 1) # Dispense 40 uL of NIS in columns 6-9 of each plate

    if count[0] != 0:
        multi.drop_tip()
    count = [-1] # reset the tip count and drop tips if used tips are attached

    # NBS dispenses
    for plate in plates:
        for well in plate.rows()[9:]:
            liq_hand(40, nbs, well, 0, [0], 1) # Dispense 40 uL of NBS in columns 10-12 of each plate

    if count[0] != 0:
        multi.drop_tip()
    count = [-1] # reset the tip count and drop tips if used tips are attached