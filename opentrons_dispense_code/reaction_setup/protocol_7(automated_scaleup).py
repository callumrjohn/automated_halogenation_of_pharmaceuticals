from opentrons import protocol_api
import math


# metadata
metadata = {
    'protocolName': 'protocol_7(automated_scaleup)',
    'author': 'Callum R. John <crj21@ic.ac.uk>',
    'description': 'Scale up reactions for GPR determined conditions where products were not isolated',
    'apiLevel': '2.9'
}

def run(protocol: protocol_api.ProtocolContext):
    
    # LABWARE

    # Pipette tip rack
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', 1)

    # Stock solution plates
    stock6 = protocol.load_labware('acme_6_wellplate_24000ul', 5) # HFIP
    stock24 = protocol.load_labware('analyticalsales_24_wellplate_80000ul', 2) # TFA and halogenating reagents
    
    # Reaction plate
    plate = protocol.load_labware('analyticalsales_48_wellplate_2000ul', 3)

    # Pipette
    p300 = protocol.load_instrument('p300_single_gen2', 'left', tip_racks = [tiprack])
    protocol.max_speeds['Z'] = 200
    
    stock24_d = 16.5

    # stocks and dimentions

    hfip = {'well' : stock6['A1'],
            'vol' : 15000} # Solvent top-up
    tfa = {'well' : stock24['A1'],
            'vol' : 6000} # TFA (4.17 M) stock solution
    pc = {'well' : stock24['A2'],
            'vol' : 5000} # Palau'chlor stock solution
    nbs = {'well' : stock24['A3'],
            'vol' : 5000} # NBS stock solution
    nis = {'well' : stock24['A4'],
           'vol' : 5000} # NIS stock solution

    # STOCK SOLUTIONS

    # TFA (4.17 M) quantities
    tfa_vols = {
    "A1": 74,
    "A2": 120,
    "A3": 36,
    "A4": 365,
    "A5": 492,
    "A6": 0,
    "A7": 199,
    "A8": 600,
    "B1": 120,
    "B2": 578,
    "B3": 600,
    "B4": 58,
    "B5": 358,
    "B6": 50,
    "B7": 0,
    "B8": 0,
    "C1": 240,
    "C2": 24,
    "C3": 48,
    "C4": 103,
    "C5": 600,
    "C6": 38,
    "C7": 41,
    "C8": 0,
    "D1": 77
    }

    # Halogenating reagent wells
    pc_vols = {
    "A1": 400,
    "A3": 400,
    "A4": 400,
    "A7": 400,
    "B1": 400,
    "B6": 400,
    "B7": 400,
    "C2": 400,
    "C6": 400
    }

    nbs_vols = {
    "A2": 400,
    "A5": 400,
    "A6": 400,
    "B4": 400,
    "B8": 400,
    "C3": 400,
    "C4": 400,
    "D1": 400
    }

    nis_vols = {
    "A8": 400,
    "B2": 400,
    "B3": 400,
    "B5": 400,
    "C1": 400,
    "C5": 400,
    "C7": 400,
    "C8": 400
    }


    # DISPENSE FUNCTIONS

    def prep300(solution, height): # Procedure to "prepare" each tip before use, ensuring accurate and consistent handling of solutions
        p300.pick_up_tip()# Pick up pipette tips

        # PRE-WETTING OF TIP
        for _ in range (2):
            p300.aspirate(100, solution.bottom(height)) # Aspirate 100uL of solution from the source well from a defined height
            p300.move_to(solution.top()) # Move to the top of the source well
            protocol.delay(seconds = 5) # Delay for 5 seconds
            p300.dispense(100, solution.top()) # Dispense 100uL of solution back into the source well
            p300.blow_out() # Blow out any remaining solution in/on the pipette tip
            
        # PRE-SAURATING OF TIP
        p300.move_to(solution.bottom(height)) # Move to the specified hieght within the source well
        p300.mix(2, 100) # Aspitate and dispense 100uL of solution 2 times


    def liq_hand(vol, asp_well, dis_well, height): # Proceedure to handle liquid transfers
        if count[0] == -1: # If the tips attached have not been used, prepare the tips
            prep300(asp_well, height)
            count[0] = 0
        if count[0] == 4:
            p300.drop_tip() # If the tips attached have been used 4 times, drop tips in the trash and prepare new tips        
            count[0] = 0
            prep300(asp_well, height)
                
        p300.aspirate(vol, asp_well.bottom(height), rate = 0.5) # Aspirate a specified volume of solution from a source well at a specified height at half the default rate (default rate = 94 uL/s)
        p300.dispense(vol, dis_well.top(), rate = 0.5) # Dispense a specified volume of solution at the top of the destination well at half the default rate (default rate = 94 uL/s)
        p300.blow_out() # Blow out any remaining solution in the pipette tip
        #print(height_t0 - height_t0*well_count[0]/total)

        count[0] = count[0] + 1 # Add 1 to the dispense count (used to determine when to drop tips and prepare new tips)


    count = [-1] # Initialise the dispense count to -1 (used to determine when to drop tips and prepare new tips)


    # HFIP dispenses
    for well, vol in tfa_vols.items(): 

        total_vol = 600 - vol # Calculate the total volume of HFIP to be transferred to each well

        if total_vol == 0:
            continue 

        # Determine the number of dispenses required to transfer the total volume of HFIP
        n_disp = 1
        disp_vol = total_vol/n_disp
        while disp_vol > 200:
            n_disp = n_disp + 1
            disp_vol = total_vol/n_disp

        # Transfer the HFIP to the destination well with mutiple dispenses if necessary
        for _ in range(n_disp):
            liq_hand(disp_vol, hfip['well'], plate[well], 0)
   
    if count[0] != 0: # Reset the tip count and drop tips if used tips are attached
        p300.drop_tip()
    count = [-1]

    # TFA dispenses
    for well, vol in tfa_vols.items():
        tfa_height = tfa['vol']/(math.pi*(stock24_d/2)**2) - 2 # Calculate the height of the TFA in the source well
        if tfa_height < 0: # Failsafe to prevent negative height
            tfa_height = 0

        total_vol = vol

        if total_vol == 0:
            continue
        
        # Determine the number of dispenses required to transfer the total volume of TFA
        n_disp = 1
        disp_vol = total_vol/n_disp
        while disp_vol > 200:
            n_disp = n_disp + 1
            disp_vol = total_vol/n_disp

        # Transfer the TFA to the destination well with mutiple dispenses if necessary
        for _ in range(n_disp):
            liq_hand(disp_vol, tfa['well'], plate[well], tfa_height)
        tfa['vol'] = tfa['vol'] - vol
    
    if count[0] != 0: # Reset the tip count and drop tips if used tips are attached
        p300.drop_tip()
    count = [-1]


    protocol.pause('Ensure substrates are dissolved before resuming') # Prior to adding halogenating reagents, ensure all substrates are dissolved before adding the halogenating reagents.


    # Palau'chlor dispenses
    for well, vol in pc_vols.items():
        pc_height = pc['vol']/(math.pi*(stock24_d/2)**2) - 2 # Calculate the height of the Palau'chlor stock in the source well
        if pc_height < 0: # Failsafe to prevent negative height
            pc_height = 0

        total_vol = vol

        # Determine the number of dispenses required to transfer the total volume of Palau'chlor
        n_disp = 1
        disp_vol = total_vol/n_disp
        while disp_vol > 200:
            n_disp = n_disp + 1
            disp_vol = total_vol/n_disp

    # Transfer the Palau'chlor to the destination well with mutiple dispenses if necessary
        for _ in range(n_disp):
            liq_hand(disp_vol, pc['well'], plate[well], pc_height)
        pc['vol'] = pc['vol'] - vol

    if count[0] != 0: # Reset the tip count and drop tips if used tips are attached
        p300.drop_tip()
    count = [-1]

    # NBS dispenses
    for well, vol in nbs_vols.items():
        nbs_height = nbs['vol']/(math.pi*(stock24_d/2)**2) - 2
        if nbs_height < 0: # Failsafe to prevent negative height
            nbs_height = 0

        # Calculate the total volume of NBS to be transferred to each well
        total_vol = vol
        n_disp = 1
        disp_vol = total_vol/n_disp
        while disp_vol > 200:
            n_disp = n_disp + 1
            disp_vol = total_vol/n_disp

        # Transfer the NBS to the destination well with mutiple dispenses if necessary
        for _ in range(n_disp):
            liq_hand(disp_vol, nbs['well'], plate[well], nbs_height)
        nbs['vol'] = nbs['vol'] - vol

    if count[0] != 0: # Reset the tip count and drop tips if used tips are attached
        p300.drop_tip()
    count = [-1]

    # NIS dispenses
    for well, vol in nis_vols.items():
        nis_height = nis['vol']/(math.pi*(stock24_d/2)**2) - 2
        if nis_height < 0: # Failsafe to prevent negative height
            nis_height = 0
        
        # Calculate the total volume of NIS to be transferred to each well
        total_vol = vol
        n_disp = 1
        disp_vol = total_vol/n_disp
        while disp_vol > 200:
            n_disp = n_disp + 1
            disp_vol = total_vol/n_disp

        # Transfer the NIS to the destination well with mutiple dispenses if necessary
        for _ in range(n_disp):
            liq_hand(disp_vol, nis['well'], plate[well], nis_height)
        nis['vol'] = nis['vol'] - vol

    if count[0] != 0: # Reset the tip count and drop tips if used tips are attached
        p300.drop_tip()
    count = [-1]
