from opentrons import protocol_api


# metadata
metadata = {
    'protocolName': 'protocol_3(stage2_0to10_nis_nbs)',
    'author': 'Callum R. John <crj21@ic.ac.uk>',
    'description': 'Protocol for screening of brominations and iodinations (0 to 10 TFA equivalents)',
    'apiLevel': '2.9'
}

def run(protocol: protocol_api.ProtocolContext):
    
    # LABWARE

    # Pipette tip racks
    tiprack1 = protocol.load_labware('opentrons_96_tiprack_300ul', 1)
    tiprack2 = protocol.load_labware('opentrons_96_tiprack_300ul', 2)
    tiprack3 = protocol.load_labware('opentrons_96_tiprack_300ul', 3)
    tiprack4 = protocol.load_labware('opentrons_96_tiprack_300ul', 4)

    # Stock solution plates
    stock96 = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 5)
    stock12 = protocol.load_labware('mettlertoledo_12_reservoir_24000ul', 6)
    
    # Reaction plates
    plate1 = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 7)
    plate2 = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 8)
    plate3 = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 10)
    plates = [plate1, plate2, plate3]
    
    # Pipette
    multi = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks = [tiprack1, tiprack2, tiprack3, tiprack4])
    protocol.max_speeds['Z'] = 60


    # STOCK SOLUTIONS

    substrates = stock96.rows()[0][0:3] # Substrate stock solution locations - A1, B1, C1: The first, second, and third columns of the stock96 plate
    substrate_vol = 1500 #ul
    sub_height_t0 = substrate_vol/(stock96['A1'].length*stock96['A1'].width) # Calculate the height of the substrate solution in eeach substrate well before the first dispense
    sub_depth_t0 = sub_height_t0 - 3 # Add a grace height of 3mm to the calculated height to ensure the pipette tip is submerged in the solution

    hfip = stock12.wells()[0] # Neat HFIP
    hfip_vol = 12000 #ul
    hfip_height_t0 = hfip_vol/(stock12['A1'].length*stock12['A1'].width) # Calculate the height of the HFIP solution in the HFIP well before the first dispense
    hfip_depth_t0 = hfip_height_t0 - 3 # Add a grace height of 3mm to the calculated height to ensure the pipette tip is submerged in the solution

    tfa_dil = stock12.wells()[1] # TFA solution (0.67 M)
    tfa_dil_vol = 5000 #ul
    tfa_dil_height_t0 = tfa_dil_vol/(stock12['A1'].length*stock12['A1'].width) # Calculate the height of the TFA solution (0.67 M) in the TFA dilute well before the first dispense
    tfa_dil_depth_t0 = tfa_dil_height_t0 - 3 # Add a grace height of 3mm to the calculated height to ensure the pipette tip is submerged in the solution

    tfa_conc = stock12.wells()[2] # TFA solution (3.33 M)
    tfa_conc_vol = 4000 #ul
    tfa_conc_height_t0 = tfa_conc_vol/(stock12['A1'].length*stock12['A1'].width) # Calculate the height of the TFA solution (3.33 M) in the TFA conc well before the first dispense
    tfa_conc_depth_t0 = tfa_conc_height_t0 - 3 # Add a grace height of 3mm to the calculated height to ensure the pipette tip is submerged in the solution

    nbs = stock12.wells()[3] # NBS solution location
    nbs_vol = 6200 #ul 
    nbs_height_t0 = nbs_vol/(stock12['A1'].length*stock12['A1'].width) # Calculate the height of the NBS solution in the NBS well before the first dispense
    nbs_depth_t0 = nbs_height_t0 - 3 # Add a grace height of 3mm to the calculated height to ensure the pipette tip is submerged in the solution

    nis = stock12.wells()[4] # NIS solution location
    nis_vol = 6200 #ul
    nis_height_t0 = nis_vol/(stock12['A1'].length*stock12['A1'].width) # Calculate the height of the NIS solution in the NIS well before the first dispense
    nis_depth_t0 = nis_height_t0 - 3 # Add a grace height of 3mm to the calculated height to ensure the pipette tip is submerged in the solution


    #counts
    substrate1_count = [0] # Global variable to count the total number of dispenses of the first column of substrate stocks
    substrate2_count = [0] # Global variable to count the total number of dispenses of the second column of substrate stocks
    substrate3_count = [0] # Global variable to count the total number of dispenses of the third column of substrate stocks
    hfip_count = [0] # Global variable to count the total number of dispenses of HFIP
    tfa_dil_count = [0] # Global variable to count the total number of dispenses of TFA solution (0.67 M)
    tfa_conc_count = [0] # Global variable to count the total number of dispenses of TFA solution (3.33 M)
    nbs_count = [0] # Global variable to count the total number of dispenses of NBS
    nis_count = [0] # Global variable to count the total number of dispenses of NIS

    #totals
    sub_total = 12 # Total number of dispenses for each substrate i.e 12 reactions being prepared with 12 dispenses of substrate
    hfip_total = 24 # Total number of dispenses of HFIP
    tfa_dil_total = 12 # Total number of dispenses of TFA solution (0.67 M)
    tfa_conc_total = 18 # Total number of dispenses of TFA solution (3.33 M)
    nbs_count_total = 18 # Total number of dispenses of NBS
    nis_count_total = 18 # Total number of dispenses of NIS


    # TFA and HFIP dispense volumes
    # dictionaries tfa and hfip quantities for each well in a row (note that an "A1" well dispenses to all wells in a column i.e. A1, B1, C1, D1, E1, F1, G1, and H1)
    hfip_quantities = {'A1': 60, 'A2': 30, 'A3': 0, 'A4': 36, 'A5': 24, 'A6': 0, 'A7': 60, 'A8': 30, 'A9': 0, 'A10': 36, 'A11': 24, 'A12': 0} # Neat HFIP
    tfa_dil_quantities = {'A1': 0, 'A2': 30, 'A3': 60, 'A4': 0, 'A5': 0, 'A6': 0, 'A7': 0, 'A8': 30, 'A9': 60, 'A10': 0, 'A11': 0, 'A12': 0} # TFA solution (0.67 M)
    tfa_conc_quantities = {'A1': 0, 'A2': 0, 'A3': 0, 'A4': 24, 'A5': 36, 'A6': 60, 'A7': 0, 'A8': 0, 'A9': 0, 'A10': 24, 'A11': 36, 'A12': 60} # TFA solution (3.33 M)


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

        count[0] = count[0] + 1 # Add 1 to the TIP dispense count (used to determine when to drop tips and prepare new tips)


    # DISPENSE PROTOCOL
    
    count = [-1] # Initialise the dispense count to -1 (used to determine when to drop tips and prepare new tips)

    # Substrate dispenses for reaction plate 1
    for wells in plate1.rows()[0]:
        liq_hand(100, substrates[0], wells, sub_depth_t0, substrate1_count, sub_total) # Dispense 100 uL of each substrate across a row within the first plate

    if count[0] != 0: # Reset the tip count and drop tips if used tips are attached
        multi.drop_tip()
    count = [-1]

    # Substrate dispenses for reaction plate 2
    for wells in plate2.rows()[0]:
        liq_hand(100, substrates[1], wells, sub_depth_t0, substrate2_count, sub_total) # Dispense 100 uL of each substrate across a row within the second plate

    if count[0] != 0: # Reset the tip count and drop tips if used tips are attached
        multi.drop_tip()
    count = [-1]

    # Substrate dispenses for reaction plate 3
    for wells in plate3.rows()[0]:
        liq_hand(100, substrates[2], wells, sub_depth_t0, substrate3_count, sub_total) # Dispense 100 uL of each substrate across a row within the third plate

    if count[0] != 0: # Reset the tip count and drop tips if used tips are attached
        multi.drop_tip()
    count = [-1]

    #HFIP dispenses
    for plate in plates: # Iterate through each plate
        for well, vol in hfip_quantities.items():
            if vol != 0:
                liq_hand(vol, hfip, plate[well], hfip_depth_t0, hfip_count, hfip_total) # Dispense HFIP solution across each plate according to the hfip_quantities dictionary
        
    if count[0] != 0: # Reset the tip count and drop tips if used tips are attached
        multi.drop_tip()
    count = [-1]  
    
    # TFA solution (0.67 M) dispenses
    for plate in plates: # Iterate through each plate
        for well, vol in tfa_dil_quantities.items():
            if vol != 0:
                liq_hand(vol, tfa_dil, plate[well], tfa_dil_depth_t0, tfa_dil_count, tfa_dil_total) # Dispense dilute TFA solution across each plate according to the tfa_dil_quantities dictionary

    if count[0] != 0:
        multi.drop_tip()
    count = [-1]

    #TFA solution (3.33 M) dispenses
    for plate in plates: # Iterate through each plate
        for well, vol in tfa_conc_quantities.items():
            if vol != 0: 
                liq_hand(vol, tfa_conc, plate[well], tfa_conc_depth_t0, tfa_conc_count, tfa_conc_total) # Dispense conc TFA solution across each plate according to the tfa_conc_quantities dictionary
    
    if count[0] != 0: # Reset the tip count and drop tips if used tips are attached
        multi.drop_tip()
    count = [-1]

    #NBS dispenses
    for plate in plates: # Iterate through each plate
        for well in plate.rows()[0][0:6]:
            liq_hand(40, nbs, well, nbs_depth_t0, nbs_count, nbs_count_total) # Dispense 40 uL of NBS in columns 1-6 of each plate
    
    if count[0] != 0:
        multi.drop_tip()
    count = [-1]

    # NIS dispenses
    for plate in plates: # Iterate through each plate
        for well in plate.rows()[0][6:12]: 
            liq_hand(40, nis, well, nis_depth_t0, nis_count, nis_count_total) # Dispense 40 uL of NIS in columns 7-12 of each plate

    if count[0] != 0:
        multi.drop_tip()
    count = [-1]